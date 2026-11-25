"""Fluxo agêntico de seleção de geometria (Parte I, Fase 2).

Grafo LangGraph: profile -> propose (LLM) -> check (regras) -> [propose | fim].
Depois de escolhida a geometria, o pedido segue para o grafo da Etapa 2
(gerador -> validador -> executor -> crítico).
"""
import json
import operator
import re
from typing import Annotated, Literal, TypedDict

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from scipy.stats import skew

from agents.audit_color import make_color_auditor
from agents.graph import run_chart
from common import FIGURES, ROOT, get_llm

OKABE = ("Norte=#0072B2, Centro=#E69F00, Lisboa e Vale do Tejo=#D55E00, "
         "Alentejo=#009E73, Algarve=#CC79A7")

# --------------------------------------------------------------------------
# Regras (heurísticas inspiradas em Wilke, caps. 6-11)
# --------------------------------------------------------------------------
LIMITS = {"bar": 12, "dot_plot": 40, "heatmap": 60, "boxplot": 25,
          "violin": 12, "ridgeline": 20, "treemap": 60}
MIN_OBS = {"violin": 15, "ridgeline": 15, "boxplot": 5}
SKEW_LIMIT = 2.0
SKEW_GEOMS = {"heatmap", "histogram_density", "boxplot", "violin", "ridgeline"}
MAX_ATTEMPTS = 3

Geometry = Literal["bar", "dot_plot", "heatmap", "histogram_density",
                   "boxplot", "violin", "ridgeline", "treemap"]


class ChartChoice(BaseModel):
    geometry: Geometry
    category_column: str = Field(description="Coluna categórica principal (grupos/linhas). "
                                 "String vazia se não aplicável.")
    second_category_column: str = Field(description="2.ª coluna categórica (colunas do heatmap, "
                                        "nível inferior do treemap). String vazia se não aplicável.")
    value_column: str = Field(description="Coluna numérica a representar.")
    top_n: int = Field(description="0 = mostrar todas as categorias; N > 0 = só as N "
                       "categorias com maior valor.")
    log_scale: bool = Field(description="True para usar escala logarítmica.")
    rationale: str = Field(description="Justificação em 2-3 frases, em português europeu, "
                           "com a cardinalidade e o volume observados.")


SYSTEM = """És um especialista em visualização de dados (Wilke, Fundamentals of Data \
Visualization, caps. 6 a 11). Recebes uma pergunta analítica e o perfil de um dataset \
(volume, cardinalidade, assimetria). Escolhes a geometria mais adequada e as colunas. \
Diretrizes:
- Quantidades por categoria: até 12 categorias -> bar; 13 a 40 -> dot_plot ordenado; \
mais de 40 -> dot_plot com top_n <= 40, ou heatmap se existir uma 2.ª dimensão categórica.
- Duas dimensões categóricas + um valor numérico -> heatmap (top_n <= 60 linhas).
- Distribuição de uma variável numérica -> histogram_density.
- Distribuição por grupos -> boxplot (muitos grupos ou poucos dados por grupo), violin \
(até 12 grupos com >= 15 observações em cada) ou ridgeline (até 20 grupos com >= 15).
- Proporções aninhadas (categoria -> subcategoria, valores positivos) -> treemap, com \
category_column = nível superior e second_category_column = nível inferior.
- Se o value_column tiver |assimetria| > 2 em distribuições ou heatmaps -> log_scale=true. \
Barras nunca em escala logarítmica.
- category_column e second_category_column são strings vazias quando não se aplicam.
Explica a escolha em 'rationale' referindo a cardinalidade e o volume observados."""


# --------------------------------------------------------------------------
# Perfil do dataset (determinístico)
# --------------------------------------------------------------------------
def profile_dataset(csv_path: str) -> dict:
    df = pd.read_csv(ROOT / csv_path)
    cols = {}
    for c in df.columns:
        s = df[c]
        is_num = (pd.api.types.is_numeric_dtype(s)
                  and not (pd.api.types.is_integer_dtype(s) and s.nunique() <= 31))
        info = {"tipo": "numerica" if is_num else "categorica",
                "n_distintos": int(s.nunique()), "n_nulos": int(s.isna().sum())}
        if is_num:
            info.update(minimo=round(float(s.min()), 3), mediana=round(float(s.median()), 3),
                        maximo=round(float(s.max()), 3),
                        assimetria=round(float(skew(s.dropna())), 2))
        else:
            counts = s.value_counts()
            info.update(exemplos=[str(v) for v in s.dropna().unique()[:4]],
                        obs_por_categoria_min=int(counts.min()),
                        obs_por_categoria_mediana=float(counts.median()))
        cols[c] = info
    return {"n_linhas": len(df), "colunas": cols}


# --------------------------------------------------------------------------
# Verificação das regras (determinística)
# --------------------------------------------------------------------------
def check_choice(c: ChartChoice, profile: dict) -> list[str]:
    cols, n_rows, g = profile["colunas"], profile["n_linhas"], c.geometry
    errs: list[str] = []

    for fname in ("category_column", "second_category_column", "value_column"):
        v = getattr(c, fname)
        if v and v not in cols:
            errs.append(f"{fname}='{v}' não existe. Colunas disponíveis: {list(cols)}")
    if errs:
        return errs
    if cols[c.value_column]["tipo"] != "numerica":
        return [f"value_column '{c.value_column}' tem de ser numérica."]
    val = cols[c.value_column]

    if g == "histogram_density":
        if c.category_column or c.second_category_column:
            errs.append("histogram_density é univariado: category_column e "
                        "second_category_column devem ficar vazios.")
        if n_rows < 30:
            errs.append("histogram_density exige pelo menos 30 observações.")
    else:
        if not c.category_column:
            errs.append(f"A geometria '{g}' exige category_column.")
        elif cols[c.category_column]["tipo"] != "categorica":
            errs.append(f"category_column '{c.category_column}' tem de ser categórica.")
    if g in ("heatmap", "treemap"):
        if not c.second_category_column:
            errs.append(f"A geometria '{g}' exige second_category_column.")
    elif c.second_category_column:
        errs.append(f"second_category_column deve ficar vazio para '{g}'.")
    if errs:
        return errs

    if c.category_column:
        cat = cols[c.category_column]
        eff = min(cat["n_distintos"], c.top_n) if c.top_n > 0 else cat["n_distintos"]
        if g in LIMITS and g != "treemap" and eff > LIMITS[g]:
            errs.append(f"'{g}' com {eff} categorias em '{c.category_column}' excede o limite "
                        f"de {LIMITS[g]}. Reduz com top_n ou escolhe outra geometria "
                        "(dot_plot até 40, heatmap até 60 linhas com 2.ª dimensão categórica).")
        if g in MIN_OBS and cat["obs_por_categoria_min"] < MIN_OBS[g]:
            errs.append(f"'{g}' exige >= {MIN_OBS[g]} observações por grupo, mas há grupos "
                        f"com {cat['obs_por_categoria_min']}. Escolhe boxplot ou menos grupos.")
    if c.second_category_column:
        sec = cols[c.second_category_column]
        if sec["tipo"] != "categorica":
            errs.append(f"second_category_column '{c.second_category_column}' tem de ser categórica.")
        elif g == "heatmap" and sec["n_distintos"] > 24:
            errs.append("Heatmap com mais de 24 colunas fica ilegível.")
        elif g == "treemap" and sec["n_distintos"] > LIMITS["treemap"]:
            errs.append("Treemap com mais de 60 folhas fica ilegível.")

    if g == "bar" and c.log_scale:
        errs.append("Barras em escala logarítmica são enganadoras: a base não é zero.")
    if g in SKEW_GEOMS and abs(val["assimetria"]) > SKEW_LIMIT and not c.log_scale:
        errs.append(f"'{c.value_column}' tem assimetria {val['assimetria']} (> {SKEW_LIMIT}): "
                    "usa log_scale=true.")
    if g == "treemap" and val["minimo"] <= 0:
        errs.append("O treemap exige valores estritamente positivos.")
    return errs


# --------------------------------------------------------------------------
# Grafo de seleção
# --------------------------------------------------------------------------
class SelState(TypedDict, total=False):
    question: str
    data_path: str
    profile: dict
    choice: dict
    errors: list[str]
    attempt: int
    history: Annotated[list[dict], operator.add]


def profile_node(state: SelState) -> dict:
    prof = profile_dataset(state["data_path"])
    print(f"[seletor] perfil: {prof['n_linhas']:,} linhas, {len(prof['colunas'])} colunas")
    return {"profile": prof, "attempt": 0, "errors": []}


def propose_node(state: SelState) -> dict:
    attempt = state["attempt"] + 1
    human = (f"Pergunta analítica: {state['question']}\n\nPerfil do dataset (JSON):\n"
             f"{json.dumps(state['profile'], ensure_ascii=False)}")
    messages = [SystemMessage(SYSTEM), HumanMessage(human)]
    if state.get("errors") and state.get("choice"):
        messages.append(HumanMessage(
            "A tua escolha anterior:\n" + json.dumps(state["choice"], ensure_ascii=False)
            + "\nfoi rejeitada pelas regras:\n- " + "\n- ".join(state["errors"])
            + "\nCorrige-a."))
    try:
        choice = get_llm(0.0).with_structured_output(ChartChoice).invoke(messages)
        if choice is None:
            raise ValueError("resposta vazia")
    except Exception as exc:
        print(f"[seletor] tentativa {attempt}: falha no LLM ({exc})")
        return {"attempt": attempt, "errors": [f"Falha na chamada ao LLM: {exc}"],
                "history": [{"attempt": attempt, "erro_llm": str(exc)}]}
    d = choice.model_dump()
    print(f"[seletor] tentativa {attempt}: {d['geometry']} "
          f"(cat={d['category_column'] or '-'}, cat2={d['second_category_column'] or '-'}, "
          f"valor={d['value_column']}, top_n={d['top_n']}, log={d['log_scale']})")
    return {"choice": d, "attempt": attempt, "errors": [],
            "history": [{"attempt": attempt, "escolha": d}]}


def check_node(state: SelState) -> dict:
    errors = state["errors"] or check_choice(ChartChoice(**state["choice"]), state["profile"])
    if errors:
        print("[seletor] regras reprovam a escolha:\n    - " + "\n    - ".join(errors))
    else:
        print("[seletor] escolha validada pelas regras")
    return {"errors": errors, "history": [{"attempt": state["attempt"], "erros": errors}]}


def after_check(state: SelState) -> str:
    if state["errors"] and state["attempt"] < MAX_ATTEMPTS:
        return "propose"
    return "end"


def build_selector_graph():
    g = StateGraph(SelState)
    g.add_node("profile", profile_node)
    g.add_node("propose", propose_node)
    g.add_node("check", check_node)
    g.add_edge(START, "profile")
    g.add_edge("profile", "propose")
    g.add_edge("propose", "check")
    g.add_conditional_edges("check", after_check, {"propose": "propose", "end": END})
    return g.compile()


def select_chart(question: str, data_path: str) -> SelState:
    return build_selector_graph().invoke(
        {"question": question, "data_path": data_path, "history": []},
        config={"recursion_limit": 30})


# --------------------------------------------------------------------------
# Da escolha à figura
# --------------------------------------------------------------------------
GUIDE = {
    "bar": ("Barras horizontais (ax.barh), da maior (no topo) para a menor, cor única "
            "(ex. #0072B2), valor escrito junto a cada barra, eixo do valor a começar em ZERO."),
    "dot_plot": ("Dot plot de Cleveland: uma categoria por linha no eixo y, ordenadas por valor "
                 "(maior no topo), um ponto por categoria (ax.scatter) com uma linha horizontal "
                 "ténue (ax.hlines) do eixo até ao ponto, cor única, grelha vertical suave. "
                 "NÃO uses barras."),
    "heatmap": ("Heatmap (ax.imshow, ax.pcolormesh ou sns.heatmap): linhas = category_column, "
                "colunas = second_category_column (meses por ordem cronológica Jan..Dez, se "
                "aplicável), linhas ordenadas pelo valor total decrescente (maior em cima); "
                "paleta SEQUENCIAL (viridis); barra de cor rotulada com unidades; sem anotações "
                "numéricas. Se log_scale=true usa matplotlib.colors.LogNorm."),
    "histogram_density": ("Histograma em densidade (não contagem) com curva KDE sobreposta "
                          "(sns.histplot(..., stat='density', kde=True)); eixo y 'Densidade'; "
                          "25 a 40 bins; linha vertical tracejada na mediana, com legenda. Se "
                          "log_scale=true, trabalha em log10(valor) e rotula o eixo x "
                          "'log10 do consumo (GWh)' (indica nota com o valor original da mediana)."),
    "boxplot": ("Boxplot por grupo (sns.boxplot) com os pontos individuais sobrepostos "
                "(sns.stripplot, semitransparentes, com jitter); grupos ordenados pela mediana; "
                "orientação horizontal se houver mais de 8 grupos. Se log_scale=true, eixo log."),
    "violin": ("Violin plot (sns.violinplot com inner='quartile', cut=0, density_norm='width') "
               "por grupo ordenado pela mediana; se os grupos forem regiões, cor por região."),
    "ridgeline": ("Ridgeline: uma curva de densidade (KDE) por grupo, empilhadas na vertical "
                  "com ligeira sobreposição (joypy.joyplot ou fill_between manual), grupos "
                  "ordenados pela mediana, eixo x partilhado, nome do grupo à esquerda."),
    "treemap": ("Treemap de 2 níveis com squarify, sem barras. Recipe: W=H=100; ordena as regiões "
                "por total decrescente; rects_reg = squarify.squarify(squarify.normalize_sizes("
                "totais_regiao, W, H), 0, 0, W, H); para cada região, ordena os seus distritos "
                "por valor decrescente e faz rects_dist = squarify.squarify(squarify."
                "normalize_sizes(valores, r['dx'], r['dy']), r['x'], r['y'], r['dx'], r['dy']); "
                "desenha com matplotlib.patches.Rectangle: cada distrito com a cor da sua região "
                "e contorno branco fino; contorno branco grosso à volta de cada região; etiqueta "
                "dentro de cada retângulo (distrito e GWh) quando houver espaço; legenda das "
                "regiões; eixos desligados."),
}

GEOM_PATTERNS = {   # (obrigatório, proibido)
    "bar": (r"\.barh?\(|sns\.barplot", None),
    "dot_plot": (r"\.scatter\(|sns\.stripplot|sns\.pointplot|\.plot\(",
                 r"\.barh?\(|sns\.barplot"),
    "heatmap": (r"imshow|pcolormesh|pcolor\(|sns\.heatmap", None),
    "histogram_density": (r"\.hist\(|histplot|kdeplot", None),
    "boxplot": (r"boxplot", None),
    "violin": (r"violinplot", None),
    "ridgeline": (r"joyplot|joypy|fill_between", None),
    "treemap": (r"squarify", None),
}


def make_geometry_validator(geometry: str):
    """Garante que o código gerado usa mesmo a geometria escolhida pelo seletor."""
    required, forbidden = GEOM_PATTERNS[geometry]

    def validate_geometry(code: str) -> list[str]:
        issues = []
        if not re.search(required, code):
            issues.append(f"O código não usa a geometria '{geometry}' escolhida pelo seletor.")
        if forbidden and re.search(forbidden, code):
            issues.append(f"Para '{geometry}' não uses barras: remove barh/bar/barplot.")
        return issues

    return validate_geometry


def build_spec(choice: dict, question: str) -> str:
    parts = [
        f"Pergunta analítica: {question}",
        f"Geometria OBRIGATÓRIA: {choice['geometry']} (escolhida por análise de cardinalidade e volume).",
        f"Colunas: categoria = {choice['category_column'] or '-'}; "
        f"2.ª categoria = {choice['second_category_column'] or '-'}; valor = {choice['value_column']}.",
    ]
    if choice["top_n"] > 0:
        parts.append(f"Mostrar apenas as {choice['top_n']} categorias de {choice['category_column']} "
                     "com maior valor total e indicá-lo no título ou numa nota.")
    if choice["log_scale"]:
        parts.append("Usar escala logarítmica (ver instruções da geometria) e indicá-la no rótulo do eixo.")
    parts.append("Instruções da geometria: " + GUIDE[choice["geometry"]])
    parts.append(f"Se a cor codificar regiões, usar exatamente: {OKABE}. "
                 "Título curto e informativo; rótulos dos eixos com unidades (GWh).")
    return "\n".join(parts)


def run_selected(name: str, data_path: str, data_description: str, question: str,
                 max_iter: int = 4):
    """Seleciona a geometria e gera a figura no grafo da Etapa 2."""
    sel = select_chart(question, data_path)
    if sel["errors"]:
        raise RuntimeError("O seletor não produziu uma escolha válida: " + "; ".join(sel["errors"]))
    choice = sel["choice"]
    spec = build_spec(choice, question)

    log_dir = FIGURES / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / f"selector_{name}.json").write_text(json.dumps(
        {"name": name, "pergunta": question, "data": data_path,
         "escolha_final": choice, "tentativas": sel["attempt"],
         "historico": sel["history"], "perfil": sel["profile"]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    validators = [make_geometry_validator(choice["geometry"]), make_color_auditor(spec, name)]
    final = run_chart(name, spec, data_path=data_path, data_description=data_description,
                      validators=validators, max_iter=max_iter)
    return choice, final