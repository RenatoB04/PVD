# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/f2_distrito.csv'
OUTPUT_PATH = 'figures/p1f2_distritos.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import pandas as pd

# Ler os dados
df = pd.read_csv(DATA_PATH)

# Selecionar e ordenar os 18 distritos por consumo total (maior no topo)
df_top = df.nlargest(18, "total_gwh").sort_values("total_gwh", ascending=True)

# Mapeamento de cores por região (paleta color-blind friendly especificada)
cores_regiao = {
    "Norte": "#0072B2",
    "Centro": "#E69F00",
    "Lisboa e Vale do Tejo": "#D55E00",
    "Alentejo": "#009E73",
    "Algarve": "#CC79A7",
}
# Caso exista alguma região fora do mapeamento, usar cinzento escuro por defeito
cores = df_top["regiao"].map(cores_regiao).fillna("#333333")

# Configurar a figura (Cleveland dot plot)
fig, ax = plt.subplots(figsize=(10, 6))

# Linhas horizontais ténues do eixo até ao ponto
ax.hlines(
    y=df_top["distrito"],
    xmin=0,
    xmax=df_top["total_gwh"],
    color="#cccccc",
    linestyle="--",
    linewidth=1,
    zorder=1,
)

# Pontos para cada distrito
ax.scatter(
    df_top["total_gwh"],
    df_top["distrito"],
    color=cores,
    s=70,
    zorder=2,
    edgecolors="none",
)

# Grelha vertical suave
ax.grid(axis="x", linestyle=":", alpha=0.5, color="#888888")
ax.set_axisbelow(True)

# Remover molduras desnecessárias (despine)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#cccccc")
ax.spines["bottom"].set_color("#cccccc")

# Rótulos e título (Claus Wilke style: limpo, informativo, em português europeu)
ax.set_xlabel("Consumo total (GWh)", fontsize=11, labelpad=10, color="#222222")
ax.set_ylabel("", fontsize=11)
ax.set_title(
    "Consumo total de energia elétrica em 2025 por distrito",
    fontsize=14,
    fontweight="bold",
    pad=15,
    loc="left",
    color="#111111",
)

# Ajustar limites do eixo X para dar margem
ax.set_xlim(left=0)

# Criar legenda manual para as regiões
from matplotlib.lines import Line2D

handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=cor,
        markersize=8,
        label=reg,
    )
    for reg, cor in cores_regiao.items()
    if reg in df_top["regiao"].values
]
ax.legend(
    handles=handles,
    title="Região",
    frameon=False,
    loc="lower right",
    fontsize=10,
    title_fontsize=10,
)

plt.tight_layout()

# Gravar e fechar figura
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
