"""Parte I, Fase 1: figuras de mapeamento estético, escalas e cor."""
from agents.audit_color import make_color_auditor
from agents.graph import run_chart

DESC_CONC = """CSV (separador vírgula), 1 linha por concelho (278), ano 2025 completo. Colunas:
- concelho (str), distrito (str)
- regiao (str): Norte, Centro, Lisboa e Vale do Tejo, Alentejo ou Algarve
- bt_gwh (float): consumo anual em baixa tensão, em GWh
- mt_gwh (float): consumo anual em MT/AT/MAT, em GWh (pode ser 0 em alguns concelhos)
- total_gwh (float): bt_gwh + mt_gwh
- quota_bt_pct (float): 100 * bt_gwh / total_gwh
- perfil (str): 'Predomínio BT' ou 'Predomínio MT/AT/MAT'
Ler com pd.read_csv(DATA_PATH)."""

DESC_DM = """CSV (separador vírgula), 1 linha por distrito e mês de 2025 (18 distritos x 12 meses). Colunas:
- distrito (str)
- mes (int 1-12), mes_nome (str: Jan, Fev, ..., Dez)
- consumo_gwh (float): consumo do distrito nesse mês, em GWh
Ler com pd.read_csv(DATA_PATH)."""

DESC_VAR = """CSV (separador vírgula), 1 linha por distrito (18). Colunas:
- distrito (str), regiao (str)
- consumo_2022_gwh, consumo_2025_gwh (float): consumo anual em GWh
- var_pct (float): variação percentual 2022 -> 2025, positiva ou negativa
Ler com pd.read_csv(DATA_PATH)."""

OKABE = ("Norte=#0072B2, Centro=#E69F00, Lisboa e Vale do Tejo=#D55E00, "
         "Alentejo=#009E73, Algarve=#CC79A7")
OKABE_HEX = ["#0072B2", "#E69F00", "#D55E00", "#009E73", "#CC79A7"]


# Validadores determinísticos (verificam o que o código consegue provar)
def requires_okabe_ito(code: str) -> list[str]:
    missing = [h for h in OKABE_HEX if h.lower() not in code.lower()]
    return [f"Faltam no código as cores exatas da paleta Okabe-Ito: {missing}"] if missing else []


def requires_centered_diverging(code: str) -> list[str]:
    issues = []
    if "TwoSlopeNorm" not in code:
        issues.append("Usa matplotlib.colors.TwoSlopeNorm(vcenter=0) para centrar a paleta.")
    if "axvline" not in code:
        issues.append("Falta a linha vertical tracejada em x = 0 (ax.axvline).")
    return issues


FIGURAS = [
    {
        "name": "p1f1_scatter_escalas",
        "data": "data/clean/p1_concelho_2025.csv",
        "desc": DESC_CONC,
        "extra": [requires_okabe_ito],
        "spec": f"""Figura com 2 painéis lado a lado (figsize (16, 7)) com o mesmo scatterplot \
dos 278 concelhos: x = bt_gwh, y = mt_gwh.
- Painel esquerdo: escala linear, título 'Escala linear'.
- Painel direito: escala logarítmica (base 10) em x e y, título 'Escala logarítmica'; excluir os \
concelhos com mt_gwh = 0 e escrever no painel quantos foram excluídos (valor calculado no código).
Mapeamentos: posição (x, y); tamanho = total_gwh (mesma escala de tamanho nos dois painéis); \
cor = regiao com exatamente este dicionário de cores hexadecimais: {OKABE}; forma = perfil \
('Predomínio BT' = círculo 'o', 'Predomínio MT/AT/MAT' = triângulo '^'). Desenha um scatter por \
grupo (região x perfil) com ax.scatter, para controlar cor e forma. alpha ~0.7.
Legendas: três legendas separadas, empilhadas na margem direita da figura e fora dos painéis \
(fig.subplots_adjust(right=0.78) e fig.legend com bbox_to_anchor): 'Região' (5 entradas), \
'Perfil' (círculo cinzento e triângulo cinzento) e 'Consumo total (GWh)' (3 tamanhos de referência). \
As legendas não se sobrepõem.
Anotações: calcular no código os 3 concelhos de maior total_gwh e anotá-los pelo nome em AMBOS os \
painéis, com seta (annotate com arrowprops) e deslocamentos diferentes para o texto não se sobrepor.
Título geral (fig.suptitle); eixos 'Consumo BT (GWh)' e 'Consumo MT/AT/MAT (GWh)'.""",
    },
    {
        "name": "p1f1_heatmap_sequencial",
        "data": "data/clean/p1_distrito_mes_2025.csv",
        "desc": DESC_DM,
        "extra": [],
        "spec": """Heatmap do consumo mensal de 2025: linhas = 18 distritos, colunas = 12 meses \
(Jan a Dez, por ordem cronológica), valor = consumo_gwh. Distritos ordenados por consumo anual \
total decrescente (maior em cima). Paleta SEQUENCIAL perceptualmente uniforme (ex.: viridis ou \
cividis) com barra de cor rotulada 'Consumo (GWh)'. Sem anotações numéricas nas células. \
Título e rótulos dos eixos em português.""",
    },
    {
        "name": "p1f1_divergente_variacao",
        "data": "data/clean/p1_distrito_variacao.csv",
        "desc": DESC_VAR,
        "extra": [requires_centered_diverging],
        "spec": """Barras horizontais (ax.barh) da variação percentual do consumo 2022 -> 2025 por \
distrito (var_pct), ordenadas de modo que a MAIOR variação apareça no TOPO e a MENOR em BAIXO. \
A cor de cada barra codifica var_pct com a paleta divergente 'PuOr' aplicada através de \
matplotlib.colors.TwoSlopeNorm(vcenter=0) (vmin e vmax simétricos: -m e +m, com m = máximo de \
|var_pct|), e uma barra de cor rotulada 'Variação (%)'. Linha vertical tracejada em x = 0 \
(ax.axvline). Limites do eixo x simétricos: ax.set_xlim(-m*1.25, m*1.25). Escrever o valor de cada \
barra (1 casa decimal, com %) junto à barra. Título e rótulos em português.""",
    },
]

if __name__ == "__main__":
    import sys

    nomes = sys.argv[1:]  # opcional: correr só algumas figuras
    resultados = {}
    for f in FIGURAS:
        if nomes and f["name"] not in nomes:
            continue
        print(f"\n{'=' * 70}\n{f['name']}\n{'=' * 70}")
        final = run_chart(f["name"], f["spec"], data_path=f["data"],
                          data_description=f["desc"],
                          validators=[make_color_auditor(f["spec"], f["name"])] + f["extra"])
        resultados[f["name"]] = (final["status"], final["iteration"])

    print("\n=== Resumo ===")
    for nome, (estado, it) in resultados.items():
        print(f"  {nome:30s} {estado:12s} {it} iteração(ões)")