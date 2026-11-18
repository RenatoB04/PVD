"""Etapa 1b: limpeza assistida por LLM.

O LLM devolve um plano estruturado (CleaningPlan). O código valida o plano
(com novas tentativas se houver erros) e aplica-o de forma determinística.
O plano fica guardado em JSON para reprodutibilidade.

Uso:
    python src/01_clean_llm.py            # reutiliza o plano guardado, se existir
    python src/01_clean_llm.py --refresh  # pede um plano novo ao LLM
"""
import argparse
import json
import re
import sys
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from common import DATA_CLEAN, DATA_RAW, get_llm

RAW_FILE = DATA_RAW / "consumos_municipio.csv"
PLAN_FILE = DATA_CLEAN / "cleaning_plan.json"
FINE_FILE = DATA_CLEAN / "consumos_freguesia.csv"
CONCELHO_FILE = DATA_CLEAN / "consumos_concelho.csv"
REPORT_FILE = DATA_CLEAN / "quality_report.md"

# Esquema final que o resto do projeto vai usar
CANONICAL = ["data", "distrito", "cod_distrito", "concelho", "cod_concelho",
             "freguesia", "cod_freguesia", "nivel_tensao", "consumo_kwh"]
TENSION_LABELS = {"BT", "MT/AT/MAT"}


# --------------------------------------------------------------------------
# 1) Esquema do plano (saída estruturada do LLM)
# --------------------------------------------------------------------------
class ColumnAction(BaseModel):
    raw_column: str = Field(description="Nome exato da coluna no ficheiro bruto.")
    action: Literal["rename", "drop"]
    new_name: str = Field(description="Nome canónico se action=rename; string vazia se drop.")
    reason: str = Field(description="Justificação curta.")


class ValueMap(BaseModel):
    raw_value: str
    clean_value: str


class NameFix(BaseModel):
    raw_name: str
    clean_name: str
    reason: str


class CleaningPlan(BaseModel):
    column_actions: list[ColumnAction]
    tension_map: list[ValueMap]
    concelho_fixes: list[NameFix]
    placeholder_prefixes: list[str]
    negative_values_action: Literal["keep", "set_nan", "drop"]
    quality_notes: list[str]


SYSTEM_PROMPT = """És um engenheiro de dados. Recebes o perfil de um dataset de \
consumos mensais de eletricidade faturados (E-REDES, Portugal continental). \
Devolves um plano de limpeza estruturado que será executado por código \
determinístico. Regras:

1. column_actions: uma entrada por cada coluna bruta, sem omitir nenhuma. \
Mapeia para o esquema canónico: data, distrito, cod_distrito, concelho, \
cod_concelho, freguesia, cod_freguesia, nivel_tensao, consumo_kwh. Colunas \
redundantes (ano, mes, mes_int, deriváveis de data) devem ser drop.
2. tension_map: converte cada valor de nível de tensão para exatamente 'BT' \
(baixa tensão) ou 'MT/AT/MAT' (média, alta e muito alta tensão).
3. concelho_fixes: apenas para nomes de concelho realmente inconsistentes \
(erros de escrita, duplicados do mesmo concelho). Lista vazia se não houver. \
Não inventes nomes.
4. placeholder_prefixes: prefixos de 'concelho' que não são municípios reais \
mas agregados residuais (consumo do distrito que não é atribuível a um concelho).
5. negative_values_action: decide o tratamento de consumos negativos \
(keep, set_nan ou drop) e justifica em quality_notes.
6. quality_notes: 4 a 8 observações curtas, em português europeu, sobre a \
qualidade dos dados, úteis para um relatório técnico."""


# --------------------------------------------------------------------------
# 2) Carregamento e perfil dos dados
# --------------------------------------------------------------------------
def load_raw() -> pd.DataFrame:
    """Lê tudo como texto e normaliza espaços."""
    df = pd.read_csv(RAW_FILE, sep=";", dtype=str)
    for col in df.columns:
        df[col] = df[col].str.strip().str.replace(r"\s+", " ", regex=True)
    return df


def build_profile(raw: pd.DataFrame) -> dict:
    """Resumo compacto do dataset bruto para enviar ao LLM."""
    columns = {
        c: {
            "n_nulos": int(raw[c].isna().sum()),
            "n_distintos": int(raw[c].nunique()),
            "exemplos": raw[c].dropna().unique()[:5].tolist(),
        }
        for c in raw.columns
    }
    energy = pd.to_numeric(raw["energia_ativa_kwh"], errors="coerce")
    n_nao_numericos = int(energy.isna().sum() - raw["energia_ativa_kwh"].isna().sum())

    por_nome = raw.groupby(["distrito", "concelho"])["coddistritoconcelho"].nunique()
    por_codigo = raw.groupby("coddistritoconcelho")["concelho"].nunique()

    return {
        "n_linhas": len(raw),
        "colunas": columns,
        "energia_ativa_kwh": {
            "n_nao_numericos": n_nao_numericos,
            "n_negativos": int((energy < 0).sum()),
            "n_zeros": int((energy == 0).sum()),
            "minimo": float(energy.min()),
            "maximo": float(energy.max()),
        },
        "nivel_de_tensao_valores": raw["nivel_de_tensao"].value_counts().to_dict(),
        "datas_distintas": sorted(raw["data"].dropna().unique().tolist()),
        "concelhos_por_distrito": {
            d: sorted(g["concelho"].dropna().unique().tolist())
            for d, g in raw.groupby("distrito")
        },
        "concelhos_com_varios_codigos": [list(i) for i in por_nome[por_nome > 1].index],
        "codigos_com_varios_nomes": por_codigo[por_codigo > 1].index.tolist(),
    }


# --------------------------------------------------------------------------
# 3) Validação do plano
# --------------------------------------------------------------------------
def rename_columns(raw: pd.DataFrame, plan: CleaningPlan) -> pd.DataFrame:
    drops = [a.raw_column for a in plan.column_actions if a.action == "drop"]
    renames = {a.raw_column: a.new_name for a in plan.column_actions
               if a.action == "rename"}
    return raw.drop(columns=drops).rename(columns=renames)


def validate_plan(plan: CleaningPlan, raw: pd.DataFrame) -> list[str]:
    """Devolve a lista de erros do plano (vazia se estiver correto)."""
    errors: list[str] = []

    # Fase A: cobertura das colunas
    covered = [a.raw_column for a in plan.column_actions]
    missing = set(raw.columns) - set(covered)
    unknown = set(covered) - set(raw.columns)
    dups = {c for c in covered if covered.count(c) > 1}
    if missing:
        errors.append(f"Colunas brutas sem ação: {sorted(missing)}")
    if unknown:
        errors.append(f"Colunas que não existem no ficheiro: {sorted(unknown)}")
    if dups:
        errors.append(f"Colunas com mais de uma ação: {sorted(dups)}")

    new_names = [a.new_name for a in plan.column_actions if a.action == "rename"]
    if sorted(new_names) != sorted(CANONICAL):
        errors.append(f"Os nomes finais têm de ser exatamente {CANONICAL}; "
                      f"recebi {sorted(new_names)}")
    if errors:
        return errors  # sem colunas corretas, não vale a pena validar o resto

    df = rename_columns(raw, plan)

    # Fase B: mapa de tensão
    existing = set(df["nivel_tensao"].dropna().unique())
    mapped = {m.raw_value for m in plan.tension_map}
    if existing - mapped:
        errors.append(f"Valores de tensão sem mapeamento: {sorted(existing - mapped)}")
    bad = {m.clean_value for m in plan.tension_map} - TENSION_LABELS
    if bad:
        errors.append(f"Rótulos de tensão inválidos {sorted(bad)}; "
                      f"só são permitidos {sorted(TENSION_LABELS)}")

    # Fase C: correções de concelho e prefixos
    concelhos = set(df["concelho"].dropna().unique())
    for fix in plan.concelho_fixes:
        if fix.raw_name not in concelhos:
            errors.append(f"concelho_fixes: '{fix.raw_name}' não existe nos dados")
    upper = df["concelho"].dropna().str.upper()
    for prefix in plan.placeholder_prefixes:
        if not upper.str.startswith(prefix.upper()).any():
            errors.append(f"placeholder_prefixes: nenhum concelho começa por '{prefix}'")

    return errors


def request_plan(raw: pd.DataFrame, max_attempts: int = 3) -> CleaningPlan:
    """Pede o plano ao LLM; se a validação falhar, devolve os erros ao LLM."""
    llm = get_llm().with_structured_output(CleaningPlan)
    profile = json.dumps(build_profile(raw), ensure_ascii=False, default=str)
    messages = [("system", SYSTEM_PROMPT),
                ("human", f"Perfil do dataset (JSON):\n{profile}")]

    last_error = ""
    for attempt in range(1, max_attempts + 1):
        print(f"[LLM] tentativa {attempt}/{max_attempts}...")
        try:
            plan = llm.invoke(messages)
            errors = validate_plan(plan, raw)
        except Exception as exc:  # resposta fora do esquema, erro de API, etc.
            plan, errors = None, [f"Falha na chamada/parsing: {exc}"]

        if not errors:
            print("[LLM] plano válido.")
            return plan

        last_error = "; ".join(errors)
        print("[LLM] plano inválido:\n  - " + "\n  - ".join(errors))
        if plan is not None:
            messages.append(("ai", plan.model_dump_json()))
        messages.append(("human", "O plano tem erros. Corrige-os e devolve o "
                                  "plano completo:\n- " + "\n- ".join(errors)))

    raise RuntimeError(f"O LLM não produziu um plano válido: {last_error}")


# --------------------------------------------------------------------------
# 4) Aplicação determinística do plano
# --------------------------------------------------------------------------
def apply_plan(raw: pd.DataFrame, plan: CleaningPlan) -> tuple[pd.DataFrame, dict]:
    log: dict = {"linhas_brutas": len(raw)}
    df = rename_columns(raw, plan)

    # Tipos
    df["data"] = pd.to_datetime(df["data"], format="%Y-%m", errors="coerce")
    df["consumo_kwh"] = pd.to_numeric(df["consumo_kwh"], errors="coerce")
    invalid = df["data"].isna() | df["consumo_kwh"].isna()
    log["removidas_data_ou_consumo_invalidos"] = int(invalid.sum())
    df = df[~invalid].copy()

    # Nível de tensão
    tmap = {m.raw_value: m.clean_value for m in plan.tension_map}
    df["nivel_tensao"] = df["nivel_tensao"].map(tmap)

    # Nomes de concelho
    fixes = {f.raw_name: f.clean_name for f in plan.concelho_fixes}
    df["concelho"] = df["concelho"].replace(fixes)
    log["concelhos_corrigidos"] = len(fixes)

    # Agregados residuais ("OUTROS ...")
    if plan.placeholder_prefixes:
        pattern = "^(" + "|".join(re.escape(p) for p in plan.placeholder_prefixes) + ")"
        df["is_outros"] = df["concelho"].str.match(pattern, case=False).fillna(False)
    else:
        df["is_outros"] = False
    df["is_outros"] = df["is_outros"].astype(bool)
    log["linhas_outros"] = int(df["is_outros"].sum())

    # Valores negativos
    negative = df["consumo_kwh"] < 0
    log["negativos_encontrados"] = int(negative.sum())
    log["negativos_acao"] = plan.negative_values_action
    if plan.negative_values_action == "set_nan":
        df.loc[negative, "consumo_kwh"] = np.nan
    elif plan.negative_values_action == "drop":
        df = df[~negative].copy()

    # Duplicados exatos
    before = len(df)
    df = df.drop_duplicates()
    log["duplicados_exatos_removidos"] = before - len(df)
    log["chaves_repetidas_data_freguesia_tensao"] = int(
        df.duplicated(subset=["data", "cod_freguesia", "nivel_tensao"]).sum()
    )

    df = df.sort_values(["data", "cod_distrito", "cod_concelho",
                         "cod_freguesia", "nivel_tensao"]).reset_index(drop=True)
    log["linhas_finais"] = len(df)
    return df, log


def aggregate_concelho(fine: pd.DataFrame) -> pd.DataFrame:
    """Soma por concelho, mês e nível de tensão (sem agregados 'OUTROS')."""
    keys = ["data", "distrito", "cod_distrito", "concelho", "cod_concelho",
            "nivel_tensao"]
    return (fine[~fine["is_outros"]]
            .groupby(keys, as_index=False)["consumo_kwh"]
            .sum(min_count=1))


# --------------------------------------------------------------------------
# 5) Relatório de qualidade
# --------------------------------------------------------------------------
def write_report(plan: CleaningPlan, log: dict,
                 fine: pd.DataFrame, conc: pd.DataFrame) -> None:
    lines = [
        "# Relatório de qualidade dos dados",
        "",
        "## Resumo",
        f"- Linhas brutas: {log['linhas_brutas']:,}",
        f"- Linhas finais (grão freguesia): {log['linhas_finais']:,}",
        f"- Linhas agregadas por concelho: {len(conc):,}",
        f"- Período: {fine['data'].min():%Y-%m} a {fine['data'].max():%Y-%m}",
        f"- Distritos: {fine['distrito'].nunique()}",
        f"- Concelhos (sem 'OUTROS'): {conc['concelho'].nunique()}",
        f"- Removidas por data/consumo inválidos: {log['removidas_data_ou_consumo_invalidos']:,}",
        f"- Linhas 'OUTROS' (marcadas, excluídas do agregado por concelho): {log['linhas_outros']:,}",
        f"- Valores negativos: {log['negativos_encontrados']:,} (ação: {log['negativos_acao']})",
        f"- Duplicados exatos removidos: {log['duplicados_exatos_removidos']:,}",
        f"- Chaves repetidas (data, freguesia, tensão): {log['chaves_repetidas_data_freguesia_tensao']:,}",
        "",
        "## Decisões do LLM sobre as colunas",
        "| Coluna bruta | Ação | Nome final | Justificação |",
        "|---|---|---|---|",
    ]
    for a in plan.column_actions:
        lines.append(f"| {a.raw_column} | {a.action} | {a.new_name or '-'} | {a.reason} |")

    lines += ["", "## Observações de qualidade (LLM)"]
    lines += [f"- {note}" for note in plan.quality_notes]
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# 6) Main
# --------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true",
                        help="Pede um plano novo ao LLM em vez de reutilizar o guardado.")
    args = parser.parse_args()

    DATA_CLEAN.mkdir(parents=True, exist_ok=True)
    raw = load_raw()
    print(f"Dataset bruto: {len(raw):,} linhas, {raw.shape[1]} colunas")

    if PLAN_FILE.exists() and not args.refresh:
        plan = CleaningPlan.model_validate_json(PLAN_FILE.read_text(encoding="utf-8"))
        errors = validate_plan(plan, raw)
        if errors:
            sys.exit("O plano guardado já não é válido: " + "; ".join(errors)
                     + "\nCorre com --refresh.")
        print(f"A reutilizar o plano guardado: {PLAN_FILE.name}")
    else:
        plan = request_plan(raw)
        PLAN_FILE.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        print(f"Plano guardado em {PLAN_FILE}")

    fine, log = apply_plan(raw, plan)
    conc = aggregate_concelho(fine)

    fine.to_csv(FINE_FILE, index=False)
    conc.to_csv(CONCELHO_FILE, index=False)
    write_report(plan, log, fine, conc)

    print("\n=== Resultado ===")
    for key, value in log.items():
        print(f"  {key}: {value:,}" if isinstance(value, int) else f"  {key}: {value}")
    print(f"\nFicheiros:\n  {FINE_FILE}\n  {CONCELHO_FILE}\n  {REPORT_FILE}")
    print("\nNotas de qualidade do LLM:")
    for note in plan.quality_notes:
        print(f"  - {note}")


if __name__ == "__main__":
    main()