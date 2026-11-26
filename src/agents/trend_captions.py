"""Prompt chaining com LangChain (Parte II, Fase 1).

Cadeia 1: estatísticas -> interpretação estruturada.
Cadeia 2: estatísticas + interpretação -> título, subtítulo e legenda.
Verificação determinística; se falhar, repete com feedback (máx. 3 tentativas).
"""
import json
import re
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from pydantic import BaseModel, Field

from common import FIGURES, get_llm


# --------------------------------------------------------------------------
# Saídas estruturadas
# --------------------------------------------------------------------------
class TrendReading(BaseModel):
    direction: Literal["crescente_ou_positiva", "decrescente_ou_negativa", "sem_tendencia_clara"]
    strength: Literal["fraca", "moderada", "forte", "nao_aplicavel"]
    main_finding: str = Field(description="Achado principal em 1-2 frases, com números das estatísticas.")
    secondary_finding: str = Field(description="Sazonalidade, ressalva de dimensão ou extremos entre regiões.")
    caveats: list[str] = Field(description="1 a 3 limitações da análise.")


class ChartText(BaseModel):
    title: str = Field(description="Título informativo com o resultado principal (máx. 100 caracteres).")
    subtitle: str = Field(description="O que o gráfico mostra: variável, período, método (máx. 140 caracteres).")
    caption: str = Field(description="Legenda de 2 a 3 frases (máx. 450 caracteres).")


# --------------------------------------------------------------------------
# Prompts
# --------------------------------------------------------------------------
SYSTEM_1 = """És um analista de dados. Recebes estatísticas JÁ CALCULADAS sobre o \
consumo de eletricidade em Portugal (E-REDES): uma série temporal mensal, uma \
associação entre duas variáveis, ou uma comparação entre regiões. NÃO recalcules nada. \
Extrai a leitura principal usando apenas factos presentes nas estatísticas.
Regras:
- direction: sinal da tendência (tendencia_pct_por_ano) ou da correlação \
(r_pearson_log). Em comparacao_regioes, o sinal predominante entre regiões. Usa \
sem_tendencia_clara se o efeito for desprezável.
- strength: pelo módulo de r (r_pearson ou r_pearson_log): abaixo de 0,3 fraca, \
de 0,3 a 0,7 moderada, acima de 0,7 forte. Em comparacao_regioes usa nao_aplicavel.
- secondary_finding: na série, a sazonalidade (mês de pico, mês de vale, amplitude); \
na correlação, a ressalva de que a associação reflete a dimensão do concelho; na \
comparação entre regiões, a região com maior e a com menor tendência.
- caveats: limitações reais (autocorrelação e p-valor indicativo, correlação não \
implica causalidade, período curto).
- Não atribuas causas externas (clima, pandemia, preços) que não estejam nos dados.
- Escreve em português europeu."""

HUMAN_1 = """Tipo de gráfico: {kind}
Estatísticas calculadas (JSON):
{stats_json}
{feedback}"""

SYSTEM_2 = """Escreves o título, o subtítulo e a legenda de um gráfico para um relatório \
técnico, em português europeu. Recebes as estatísticas calculadas e a interpretação \
extraída. Regras:
- title: afirmação informativa com o resultado principal (máx. 100 caracteres).
- subtitle: o que o gráfico mostra (variável, período, método), máx. 140 caracteres.
- caption: 2 a 3 frases, máx. 450 caracteres: resultado com números, sazonalidade ou \
ressalva, e a limitação principal.
- Todos os números que escreveres têm de existir nas estatísticas, no máximo com 1 \
casa decimal, com vírgula decimal e sem separador de milhares. Não escrevas limiares \
de p-valor nem números que não estejam nas estatísticas.
- Não inventes causas nem uses a palavra 'significativo' sem p_valor abaixo de 0,05.
- Sem aspas nem quebras de linha."""

HUMAN_2 = """Tipo de gráfico: {kind}
Estatísticas calculadas (JSON):
{stats_json}
Interpretação extraída (JSON):
{reading_json}
{feedback}"""

PROMPT_1 = ChatPromptTemplate.from_messages([("system", SYSTEM_1), ("human", HUMAN_1)])
PROMPT_2 = ChatPromptTemplate.from_messages([("system", SYSTEM_2), ("human", HUMAN_2)])


def build_pipeline():
    llm = get_llm(0.0)
    chain1 = PROMPT_1 | llm.with_structured_output(TrendReading)
    chain2 = PROMPT_2 | llm.with_structured_output(ChartText)
    return (RunnablePassthrough.assign(reading=chain1)
            | RunnableLambda(lambda d: {**d, "reading_json": d["reading"].model_dump_json()})
            | RunnablePassthrough.assign(text=chain2))


# --------------------------------------------------------------------------
# Verificação determinística
# --------------------------------------------------------------------------
NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")


def collect_numbers(obj, acc: set | None = None) -> set:
    acc = set() if acc is None else acc
    if isinstance(obj, dict):
        for v in obj.values():
            collect_numbers(v, acc)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            collect_numbers(v, acc)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        acc.add(abs(float(obj)))
    return acc


def check_numbers(text: str, stats: dict) -> list[str]:
    """Todos os números do texto têm de existir nas estatísticas (isentos: anos e inteiros 1-12)."""
    allowed = collect_numbers(stats)
    bad = []
    for token in NUM_RE.findall(text):
        x = float(token.replace(",", "."))
        has_dec = bool(re.search(r"[.,]", token))
        if not has_dec and (1 <= x <= 12 or 2019 <= x <= 2027):
            continue
        tol = 0.051 if has_dec else 0.51
        if not any(abs(x - a) <= tol for a in allowed):
            bad.append(token)
    return [f"Números que não existem nas estatísticas: {sorted(set(bad))}"] if bad else []


def expected_strength(r: float) -> str:
    a = abs(r)
    return "fraca" if a < 0.3 else "moderada" if a < 0.7 else "forte"


def check_output(reading: TrendReading, text: ChartText, stats: dict,
                 sign: float | None, r: float | None) -> list[str]:
    errs = []
    if len(text.title) > 100:
        errs.append(f"Título com {len(text.title)} caracteres (máx. 100).")
    if len(text.subtitle) > 140:
        errs.append(f"Subtítulo com {len(text.subtitle)} caracteres (máx. 140).")
    if len(text.caption) > 450:
        errs.append(f"Legenda com {len(text.caption)} caracteres (máx. 450).")
    errs += check_numbers(" ".join([text.title, text.subtitle, text.caption]), stats)
    if sign is not None:
        if reading.direction == "crescente_ou_positiva" and sign < 0:
            errs.append("A direção 'crescente_ou_positiva' contradiz o sinal negativo das estatísticas.")
        if reading.direction == "decrescente_ou_negativa" and sign > 0:
            errs.append("A direção 'decrescente_ou_negativa' contradiz o sinal positivo das estatísticas.")
    if r is not None and reading.strength != expected_strength(r):
        errs.append(f"Com |r| = {abs(r):.2f} a força correta é '{expected_strength(r)}', "
                    f"não '{reading.strength}'.")
    return errs


# --------------------------------------------------------------------------
# Execução com repetição e feedback
# --------------------------------------------------------------------------
def generate_texts(name: str, kind: str, stats: dict, sign: float | None = None,
                   r: float | None = None, max_attempts: int = 3) -> dict:
    pipeline = build_pipeline()
    stats_json = json.dumps(stats, ensure_ascii=False)
    feedback, attempts, result = "", [], None

    for n in range(1, max_attempts + 1):
        print(f"[cadeia:{name}] tentativa {n}/{max_attempts}")
        reading = text = None
        try:
            out = pipeline.invoke({"kind": kind, "stats_json": stats_json, "feedback": feedback})
            reading, text = out["reading"], out["text"]
            problems = check_output(reading, text, stats, sign, r)
        except Exception as exc:
            problems = [f"Falha na cadeia: {exc}"]

        attempts.append({"tentativa": n,
                         "interpretacao": reading.model_dump() if reading else None,
                         "texto": text.model_dump() if text else None,
                         "problemas": problems})
        if not problems:
            print(f"[cadeia:{name}] validada.")
            result = {"title": text.title, "subtitle": text.subtitle, "caption": text.caption,
                      "reading": reading.model_dump(), "tentativas": n}
            break
        print("    rejeitada:\n      - " + "\n      - ".join(problems))
        feedback = ("ATENÇÃO: a tentativa anterior foi rejeitada: " + "; ".join(problems)
                    + ". Corrige estes pontos usando apenas as estatísticas fornecidas.")

    log_dir = FIGURES / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / f"captions_{name}.json").write_text(json.dumps(
        {"name": name, "kind": kind, "stats": stats, "tentativas": attempts},
        ensure_ascii=False, indent=2), encoding="utf-8")

    if result is None:
        raise RuntimeError(f"A cadeia '{name}' não produziu um texto válido em {max_attempts} tentativas.")
    return result