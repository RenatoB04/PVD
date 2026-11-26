"""Parte II, Fase 2: integridade de eixos, tratamento de sobreposição e contraexemplo.

Uso:
    python src/parte2_fase2.py                      # as 3 figuras
    python src/parte2_fase2.py p2f2_sobreposicao    # só algumas
"""
import sys

from agents.audit_color import make_color_auditor
from agents.graph import run_chart
from agents.integrity_check import check_bar_axis_integrity
from parte2_fase1 import requires

DESC_ANUAL = """CSV (separador vírgula), 1 linha por ano completo (2021 a 2025). Colunas:
- ano (int)
- bt_gwh, mt_gwh, total_gwh (float): consumo anual nacional em baixa tensão, em MT/AT/MAT e total, em GWh
- var_pct (float): variação percentual do total face ao ano anterior (NaN em 2021)
Ler com pd.read_csv(DATA_PATH)."""

DESC_CM = """CSV (separador vírgula), 1 linha por concelho e mês (278 concelhos x 69 meses, 2020-11 a 2026-07). Colunas:
- concelho, distrito, regiao (str)
- data: primeiro dia do mês
- bt_gwh, mt_gwh (float): consumo mensal do concelho em baixa tensão e em MT/AT/MAT, em GWh (pode ser 0)
Ler com pd.read_csv(DATA_PATH, parse_dates=['data'])."""

FIGURAS = [
    {
        "name": "p2f2_barras_anual", "data": "data/clean/p2_anual_nacional.csv", "desc": DESC_ANUAL,
        "extra": [check_bar_axis_integrity,
                  requires((r"\.bar\(|barplot", "O gráfico tem de ser de barras verticais (ax.bar)."))],
        "critic": True,
        "spec": """Gráfico de barras verticais (ax.bar) do consumo anual total nacional (total_gwh) de \
2021 a 2025 (5 anos completos), figsize (10, 6.5), cor única #0072B2. O eixo y (métrico) começa \
obrigatoriamente em zero: ax.set_ylim(0, total.max() * 1.15). Rótulo do eixo y 'Consumo anual (GWh)'; eixo x \
com os anos como texto e rótulo 'Ano'. Escrever o valor de cada barra acima dela (GWh, sem casas decimais, \
separador de milhares por espaço: f"{v:,.0f}".replace(",", " ")). Dentro de cada barra, junto ao topo e a \
branco, a variação face ao ano anterior (var_pct, 1 casa decimal, sinal explícito, vírgula decimal) para 2022 a \
2025; 2021 sem variação. Título 'Consumo anual de eletricidade em Portugal continental, 2021–2025'. Nota no \
rodapé (fig.text, fontsize 9, cinzento): 'Anos completos; 2020 e 2026 excluídos por estarem incompletos. Eixo \
vertical a partir de zero.' Sem legenda e sem grelha vertical.""",
    },
    {
        # Contraexemplo INTENCIONAL (só para o relatório): sem nó de integridade e sem crítico,
        # porque ambos tentariam "corrigir" o defeito que se pretende mostrar.
        "name": "p2f2_contraexemplo_truncado", "data": "data/clean/p2_anual_nacional.csv",
        "desc": DESC_ANUAL, "extra": [], "critic": False,
        "spec": """Figura com 2 painéis lado a lado (figsize (13, 6.5)) com as MESMAS barras verticais \
(ax.bar) do consumo anual total nacional (total_gwh) de 2021 a 2025, cor #0072B2.
- Painel esquerdo, título 'Contraexemplo: eixo truncado (distorce as magnitudes)': \
ax.set_ylim(0.97 * total.min(), 1.01 * total.max()).
- Painel direito, título 'Correto: eixo a partir de zero': ax.set_ylim(0, total.max() * 1.15).
Os dois painéis têm o rótulo y 'Consumo anual (GWh)' e os anos no eixo x. Em cada painel, uma caixa de texto \
no canto superior com a 'razão visual' = (altura visível da maior barra) / (altura visível da menor barra), \
calculada com o limite inferior do eixo (ymin): (max - ymin) / (min - ymin), e a 'razão real' = max / min \
(2 casas decimais, sufixo 'x', vírgula decimal). Título geral (fig.suptitle): 'Princípio da tinta \
proporcional: a altura da barra tem de ser proporcional ao valor'.""",
    },
    {
        "name": "p2f2_sobreposicao", "data": "data/clean/p2_concelho_mes_bt_mt.csv", "desc": DESC_CM,
        "extra": [requires((r"hexbin|hist2d", "Usa ax.hexbin (ou hist2d) no 3.º painel."),
                           (r"alpha\s*=", "Usa transparência (alpha) no 2.º painel."))],
        "critic": True,
        "spec": """Figura com 3 painéis lado a lado (figsize (18, 6.2), sharex=True, sharey=True) com os \
mesmos dados: cada ponto é um concelho num mês (x = bt_gwh, y = mt_gwh), usando apenas linhas com bt_gwh > 0 e \
mt_gwh > 0; escalas logarítmicas (base 10) nos dois eixos. Painel 1 'Pontos opacos (sobreposição)': ax.scatter \
com s=10, alpha=1, cor #0072B2, linewidths=0. Painel 2 'Pontos transparentes': ax.scatter com s=10, alpha=0.08, \
cor #0072B2, linewidths=0. Painel 3 'Hexbin (contagem por célula)': ax.hexbin(x, y, gridsize=55, xscale='log', \
yscale='log', bins='log', mincnt=1, cmap='viridis') com barra de cor rotulada 'Nº de observações (escala log)', \
fora dos gráficos. Rótulos dos eixos 'Consumo BT (GWh)' e 'Consumo MT/AT/MAT (GWh)' (y só no 1.º painel). \
Calcular no código o nº de observações usadas e o nº excluídas por terem BT ou MT igual a zero, e escrevê-los \
no título geral (fig.suptitle) em 2 linhas: 'Tratamento de sobreposição de pontos (Wilke, cap. 18)' e \
'n = X observações concelho-mês usadas; Y excluídas (consumo nulo)'.""",
    },
]

if __name__ == "__main__":
    nomes = sys.argv[1:]
    resumo = []
    for f in FIGURAS:
        if nomes and f["name"] not in nomes:
            continue
        print(f"\n{'=' * 70}\n{f['name']}\n{'=' * 70}")
        final = run_chart(f["name"], f["spec"], data_path=f["data"], data_description=f["desc"],
                          validators=[make_color_auditor(f["spec"], f["name"])] + f["extra"],
                          use_critic=f["critic"])
        resumo.append((f["name"], final["status"], final["iteration"]))

    print("\n=== Resumo ===")
    for nome, estado, it in resumo:
        print(f"  {nome:30s} {estado:12s} {it} iteração(ões)")