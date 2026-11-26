"""Parte II, Fase 1: prompt chaining (títulos/legendas) + figuras de correlação e séries.

Uso:
    python src/parte2_fase1.py                       # textos (se não existirem) + 4 figuras
    python src/parte2_fase1.py p2f1_serie_nacional   # só algumas figuras
    python src/parte2_fase1.py --refresh-texts       # refaz os textos com o LLM
"""
import json
import re
import sys

import pandas as pd

from agents.audit_color import make_color_auditor
from agents.chart_selector import OKABE, legend_outside
from agents.graph import run_chart
from agents.trend_captions import generate_texts
from agents.trend_stats import correlation_stats, region_stats, series_stats
from common import DATA_CLEAN
from parte1_fase1 import DESC_CONC

TEXTS_FILE = DATA_CLEAN / "p2f1_texts.json"
TEXTS_REL = "data/clean/p2f1_texts.json"

DESC_NAC = """CSV (separador vírgula), série mensal nacional, 69 linhas (2020-11 a 2026-07). Colunas:
- data: primeiro dia do mês (ler com parse_dates=['data'])
- bt_gwh, mt_gwh (float): consumo mensal em baixa tensão e em MT/AT/MAT, em GWh
- total_gwh (float): bt_gwh + mt_gwh, em GWh
Ler com pd.read_csv(DATA_PATH, parse_dates=['data'])."""

DESC_REG = """CSV (separador vírgula), série mensal por região em formato longo (5 regiões x 69 meses). Colunas:
- data: primeiro dia do mês (ler com parse_dates=['data'])
- regiao (str): Norte, Centro, Lisboa e Vale do Tejo, Alentejo ou Algarve
- consumo_gwh (float): consumo mensal da região em GWh
Ler com pd.read_csv(DATA_PATH, parse_dates=['data'])."""


# --------------------------------------------------------------------------
# Fase 1: estatísticas + prompt chaining
# --------------------------------------------------------------------------
def stage_texts(refresh: bool) -> dict:
    texts = {}
    if TEXTS_FILE.exists() and not refresh:
        texts = json.loads(TEXTS_FILE.read_text(encoding="utf-8"))

    nac = (pd.read_csv(DATA_CLEAN / "p2_serie_nacional.csv", parse_dates=["data"])
           .set_index("data")["total_gwh"])
    reg = pd.read_csv(DATA_CLEAN / "p2_serie_regiao.csv", parse_dates=["data"])
    conc = pd.read_csv(DATA_CLEAN / "p1_concelho_2025.csv")

    jobs = {  # chave: (tipo, estatísticas, chave do sinal, chave de r)
        "scatter": ("correlacao",
                    {**correlation_stats(conc),
                     "variavel_x": "consumo anual de eletricidade em baixa tensão (BT), por concelho, em 2025",
                     "variavel_y": "consumo anual de eletricidade em MT/AT/MAT, por concelho, em 2025"},
                    "r_pearson_log", "r_pearson_log"),
        "serie_nacional": ("serie_temporal",
                           {**series_stats(nac),
                            "variavel": "consumo mensal total de eletricidade em Portugal continental (GWh)",
                            "metodo": "regressão linear sobre a série dessazonalizada (decomposição STL)"},
                           "tendencia_pct_por_ano", "r_pearson"),
        "regioes": ("comparacao_regioes",
                    {"variavel": "consumo mensal de eletricidade por região (GWh)",
                     "metodo": "regressão linear sobre a série dessazonalizada (STL) de cada região",
                     "regioes": region_stats(reg)},
                    None, None),
    }
    for key, (kind, stats, sign_key, r_key) in jobs.items():
        print(f"\n[estatísticas:{key}]\n{json.dumps(stats, ensure_ascii=False, indent=2)}")
        if key in texts:
            print(f"[textos] '{key}' já existe (usa --refresh-texts para refazer)")
            continue
        res = generate_texts(key, kind, stats,
                             sign=stats[sign_key] if sign_key else None,
                             r=stats[r_key] if r_key else None)
        texts[key] = {**res, "stats": stats}
        TEXTS_FILE.write_text(json.dumps(texts, ensure_ascii=False, indent=2), encoding="utf-8")
    return texts


# --------------------------------------------------------------------------
# Validadores
# --------------------------------------------------------------------------
def requires(*checks: tuple[str, str]):
    """Cada verificação = (regex, mensagem específica para o gerador)."""
    def validate(code: str) -> list[str]:
        return [msg for pattern, msg in checks if not re.search(pattern, code)]
    validate.__name__ = "requires_check"
    return validate


def uses_texts(key: str):
    return requires(
        (r"p2f1_texts\.json", f"Lê os textos de {TEXTS_REL} com json.load(open(..., encoding='utf-8'))."),
        (rf"""['"]{key}['"]""", f"Acede à chave '{key}' do JSON dos textos."),
        (r"""['"]title['"]""", "Usa o campo 'title' do JSON como título."),
        (r"""['"]subtitle['"]""", "Usa o campo 'subtitle' do JSON como subtítulo."),
        (r"""['"]caption['"]""", "Usa o campo 'caption' do JSON como legenda."),
        (r"utf-8", "Abre o JSON com encoding='utf-8'."),
    )


def text_block(key: str, texts: dict) -> str:
    t = texts[key]
    return (f"TEXTOS (obrigatório): carrega o ficheiro assim: "
            f"T = json.load(open('{TEXTS_REL}', encoding='utf-8'))['{key}']. "
            "O título, o subtítulo e a legenda NÃO se escrevem à mão: usa T['title'], T['subtitle'] e "
            "T['caption']; as estatísticas calculadas estão em T['stats'] (dicionário). "
            "Layout: título com fig.suptitle (fontsize 14, bold, x=0.01, ha='left'); subtítulo logo abaixo "
            "com fig.text (fontsize 10, cinzento); legenda no rodapé com fig.text e "
            "textwrap.fill(width=120), fontsize 9. Reserva espaço para estes três blocos "
            "(fig.subplots_adjust com top e bottom adequados) sem sobreposição.\n"
            f"Para referência, o conteúdo atual é: título='{t['title']}'; subtítulo='{t['subtitle']}'; "
            f"legenda='{t['caption']}'")


ROLLING = (r"rolling\(\s*(?:window\s*=\s*)?12", "Calcula a média móvel com .rolling(12, center=True).")
LOWESS = (r"lowess", "Calcula a curva LOWESS com statsmodels (lowess, frac=0.3, return_sorted=False).")


def build_figuras(texts: dict) -> list[dict]:
    return [
        {
            "name": "p2f1_scatter_correlacao", "data": "data/clean/p1_concelho_2025.csv",
            "desc": DESC_CONC,
            "extra": [uses_texts("scatter"),
                      requires((r"polyfit", "Calcula a reta de regressão em log-log com np.polyfit."),
                               (r"r_pearson_log", "Lê stats['r_pearson_log'] do JSON, sem recalcular."),
                               (r"rho_spearman", "Lê stats['rho_spearman'] do JSON, sem recalcular."))],
            "spec": f"""Scatterplot dos concelhos (figsize (11, 9)). Logo a seguir a ler o CSV, filtra: \
d = df[(df['bt_gwh'] > 0) & (df['mt_gwh'] > 0)] e usa SEMPRE d (scatter e polyfit), porque log10(0) é infinito. \
x = bt_gwh, y = mt_gwh, ambos em escala logarítmica (ax.set_xscale('log'), ax.set_yscale('log')). Um \
ax.scatter por região (s=35, alpha=0.75), com exatamente estas cores: {OKABE}. Reta de regressão em log-log: \
a, b = np.polyfit(np.log10(d['bt_gwh']), np.log10(d['mt_gwh']), 1), desenhada a tracejado preto ao longo do \
intervalo de x (10**(a*log10(x)+b)). Caixa de texto dentro do gráfico (canto superior esquerdo, fundo branco \
semitransparente) com valores lidos de stats = T['stats']: r de Pearson (log-log) = stats['r_pearson_log'], \
rho de Spearman = stats['rho_spearman'] e n = stats['n_concelhos'] (2 casas decimais nos coeficientes). \
Eixos 'Consumo BT (GWh)' e 'Consumo MT/AT/MAT (GWh)'. Legenda das regiões FORA do gráfico (bbox_to_anchor, à \
direita). Os dados são o ano de 2025.
{text_block('scatter', texts)}""",
        },
        {
            "name": "p2f1_serie_nacional", "data": "data/clean/p2_serie_nacional.csv", "desc": DESC_NAC,
            "extra": [uses_texts("serie_nacional"), requires(LOWESS, ROLLING)],
            "spec": f"""Gráfico de linhas (figsize (12, 7.5)) do consumo mensal total nacional \
(total_gwh), 2020-11 a 2026-07. Camadas: (1) série observada, linha fina cinzenta (#999999) com pequenos \
pontos; (2) média móvel centrada de 12 meses (rolling(12, center=True)), linha #0072B2 de espessura 2; \
(3) curva LOWESS (statsmodels.nonparametric.smoothers_lowess.lowess com frac=0.3, x = 0..n-1, \
return_sorted=False), linha #D55E00 de espessura 2.5. Eixo x com datas (uma marca por ano, formato %Y), \
rótulo 'Data'; eixo y 'Consumo mensal (GWh)'. Grelha horizontal suave. Legenda das três linhas \
('Observado', 'Média móvel 12 meses', 'LOWESS') FORA da área do gráfico, por baixo (bbox_to_anchor).
{text_block('serie_nacional', texts)}""",
        },
        {
            "name": "p2f1_regioes_indice", "data": "data/clean/p2_serie_regiao.csv", "desc": DESC_REG,
            "extra": [uses_texts("regioes"), requires(ROLLING)],
            "spec": f"""Gráfico de linhas (figsize (12, 7.5)): índice do consumo mensal de cada uma das \
5 regiões, com base 100 = média dos 12 meses de 2022 dessa região. Passos: pivot (data x regiao) com \
consumo_gwh; dividir pela média de 2022 de cada região e multiplicar por 100; suavizar com média móvel \
centrada de 12 meses (rolling(12, center=True)). Uma linha por região (espessura 2) com exatamente estas \
cores: {OKABE}. Linha horizontal tracejada cinzenta em y = 100. Eixo x com uma marca por ano (formato %Y), \
rótulo 'Data'; eixo y 'Índice de consumo (2022 = 100, média móvel de 12 meses)'. Legenda das regiões FORA \
do gráfico, à direita.
{text_block('regioes', texts)}""",
        },
        {
            "name": "p2f1_comparacao_suavizacao", "data": "data/clean/p2_serie_nacional.csv",
            "desc": DESC_NAC,
            "extra": [requires((r"polyfit|linregress", "Ajusta a tendência linear com np.polyfit (grau 1)."),
                               ROLLING, LOWESS)],
            "spec": """Figura com 3 painéis lado a lado (1 linha, 3 colunas, figsize (16, 5.5), \
sharey=True). Cada painel mostra a série mensal nacional (total_gwh) em cinzento claro (#BBBBBB) e um \
modelo sobreposto (espessura 2.5): (1) 'Tendência linear' (np.polyfit grau 1 sobre o índice 0..n-1), cor \
#009E73; (2) 'Média móvel centrada de 12 meses' (rolling(12, center=True)), cor #0072B2; (3) 'LOWESS \
(frac = 0,3)' (statsmodels lowess, frac=0.3, return_sorted=False), cor #D55E00. Título de cada painel = \
nome do modelo; título geral (fig.suptitle) 'Três modelos aplicados ao consumo mensal nacional'. Eixo y \
'Consumo mensal (GWh)' só no primeiro painel; eixo x com uma marca por ano (formato %Y). Sem legendas \
(os títulos dos painéis chegam).""",
        },
    ]


if __name__ == "__main__":
    args = sys.argv[1:]
    refresh = "--refresh-texts" in args
    nomes = [a for a in args if not a.startswith("--")]

    texts = stage_texts(refresh)
    resumo = []
    for f in build_figuras(texts):
        if nomes and f["name"] not in nomes:
            continue
        print(f"\n{'=' * 70}\n{f['name']}\n{'=' * 70}")
        final = run_chart(f["name"], f["spec"], data_path=f["data"], data_description=f["desc"],
                          validators=[make_color_auditor(f["spec"], f["name"]), legend_outside] + f["extra"])
        resumo.append((f["name"], final["status"], final["iteration"]))

    print("\n=== Resumo ===")
    for nome, estado, it in resumo:
        print(f"  {nome:30s} {estado:12s} {it} iteração(ões)")