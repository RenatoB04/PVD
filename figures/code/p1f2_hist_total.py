# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_concelho_2025.csv'
OUTPUT_PATH = 'figures/p1f2_hist_total.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import pandas as pd

# Ler os dados
df = pd.read_csv(DATA_PATH)

# Selecionar os 40 concelhos com maior consumo anual total e ordenar (maior no topo)
df_top40 = df.nlargest(40, "total_gwh").sort_values("total_gwh", ascending=True)

# Mapeamento de cores por região (especificação exata)
cores_regiao = {
    "Norte": "#0072B2",
    "Centro": "#E69F00",
    "Lisboa e Vale do Tejo": "#D55E00",
    "Alentejo": "#009E73",
    "Algarve": "#CC79A7",
}

# Criar a figura
fig, ax = plt.subplots(figsize=(10, 10))

# Extrair dados para o plot
y_pos = range(len(df_top40))
concelhos = df_top40["concelho"]
valores = df_top40["total_gwh"]
regioes = df_top40["regiao"]
cores = regioes.map(cores_regiao)

# Dot plot de Cleveland (linhas horizontais finas e pontos)
ax.hlines(
    y=y_pos,
    xmin=valores.min() * 0.8,
    xmax=valores,
    color="#cccccc",
    linestyle="-",
    linewidth=1,
    zorder=1,
)
scatter = ax.scatter(
    valores, y_pos, color=cores, s=50, zorder=2, edgecolors="none"
)

# Configurar escala logarítmica no eixo x
ax.set_xscale("log")

# Rótulos e título em português europeu
ax.set_yticks(y_pos)
ax.set_yticklabels(concelhos, fontsize=9)
ax.set_xlabel("Consumo anual total (GWh, escala logarítmica)", fontsize=11)
ax.set_title(
    "Os 40 concelhos com maior consumo de eletricidade (2025)",
    fontsize=13,
    pad=15,
    fontweight="bold",
)

# Grelha suave vertical
ax.grid(
    axis="x", which="both", linestyle="--", linewidth=0.5, color="#e0e0e0", zorder=0
)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#cccccc")
ax.spines["bottom"].set_color("#cccccc")

# Legenda para as regiões
handles = [
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=cor,
        markersize=8,
        label=regiao,
    )
    for regiao, cor in cores_regiao.items()
]
ax.legend(
    handles=handles,
    title="Região",
    loc="lower right",
    frameon=True,
    facecolor="white",
    edgecolor="none",
)

# Ajustes finais de layout
plt.tight_layout()

# Guardar e fechar
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
