# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_concelho_2025.csv'
OUTPUT_PATH = 'figures/p1f2_concelhos.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import pandas as pd

# Ler os dados
df = pd.read_csv(DATA_PATH)

# Selecionar os 30 concelhos com maior consumo total e ordenar do menor para o maior
# (para que o maior fique no topo após a inversão do eixo y)
df_top30 = df.nlargest(30, "total_gwh").sort_values("total_gwh", ascending=True)

# Mapeamento de cores conforme especificação
cores_regiao = {
    "Norte": "#0072B2",
    "Centro": "#E69F00",
    "Lisboa e Vale do Tejo": "#D55E00",
    "Alentejo": "#009E73",
    "Algarve": "#CC79A7",
}

# Atribuir cores com base na região
cump_cores = df_top30["regiao"].map(cores_regiao).fillna("#7f7f7f")

# Criar a figura
fig, ax = plt.subplots(figsize=(10, 8))

# Dot plot de Cleveland: linhas horizontais e pontos
ax.hlines(
    y=df_top30["concelho"],
    xmin=0,
    xmax=df_top30["total_gwh"],
    color="#d9d9d9",
    linewidth=1.2,
    zorder=1,
)

scatter = ax.scatter(
    df_top30["total_gwh"],
    df_top30["concelho"],
    c=cump_cores,
    s=55,
    zorder=2,
    edgecolors="none",
)

# Grelha suave no eixo x
ax.xaxis.grid(True, linestyle="--", alpha=0.5, color="#cccccc")
ax.set_axisbelow(True)

# Rótulos e título em português europeu
ax.set_xlabel("Consumo total de eletricidade (GWh)", fontsize=11, labelpad=10)
ax.set_ylabel("Concelho", fontsize=11, labelpad=10)
ax.set_title(
    "Os 30 concelhos com maior consumo de eletricidade em 2025",
    fontsize=13,
    pad=15,
    fontweight="bold",
    loc="left",
)

# Ajustes visuais
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#cccccc")
ax.spines["bottom"].set_color("#cccccc")
ax.tick_params(axis="both", which="both", length=0)

# Legenda manual para as regiões presentes no top 30
regioes_presentes = df_top30["regiao"].unique()
handles = [
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=cores_regiao[r],
        markersize=8,
        label=r,
    )
    for r in cores_regiao.keys()
    if r in regioes_presentes
]
ax.legend(
    handles=handles,
    title="Região",
    frameon=False,
    loc="lower right",
    fontsize=10,
    title_fontsize=10,
)

# Garantir margens adequadas
plt.tight_layout()

# Gravar a figura
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
