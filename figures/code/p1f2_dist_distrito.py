# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_concelho_2025.csv'
OUTPUT_PATH = 'figures/p1f2_dist_distrito.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Configuração de estilo inspirada em Claus Wilke
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.family"] = "sans-serif"

# Carregar dados
df = pd.read_csv(DATA_PATH)

# Calcular a mediana da quota_bt_pct por distrito para ordenação
ordem_distritos = (
    df.groupby("distrito")["quota_bt_pct"]
    .median()
    .sort_values(ascending=True)
    .index
)

# Criar a figura
fig, ax = plt.subplots(figsize=(10, 8))

# Dicionário de cores para as regiões conforme especificado
cores_regioes = {
    "Norte": "#0072B2",
    "Centro": "#E69F00",
    "Lisboa e Vale do Tejo": "#D55E00",
    "Alentejo": "#009E73",
    "Algarve": "#CC79A7",
}

# Mapear a região dominante para cada distrito ordenado para colorir os boxplots e pontos
# Usamos a primeira ocorrência da região para cada distrito (assumindo que cada distrito pertence a uma única região)
mapa_distrito_regiao = (
    df.drop_duplicates(subset=["distrito"])
    .set_index("distrito")["regiao"]
    .to_dict()
)
paleta_distritos = [
    cores_regioes[mapa_distrito_regiao[d]] for d in ordem_distritos
]

# Como são mais de 8 grupos (18 distritos), usar orientação horizontal
# Boxplot
sns.boxplot(
    data=df,
    x="quota_bt_pct",
    y="distrito",
    order=ordem_distritos,
    ax=ax,
    palette=paleta_distritos,
    boxprops=dict(alpha=0.7),
    fliersize=0,  # Ocultar outliers do boxplot para não duplicar com o stripplot
    linewidth=1.2,
)

# Stripplot sobreposto (pontos individuais)
sns.stripplot(
    data=df,
    x="quota_bt_pct",
    y="distrito",
    order=ordem_distritos,
    ax=ax,
    color="black",
    alpha=0.4,
    size=4,
    jitter=0.2,
)

# Legenda para as regiões (fora da área dos dados)
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
    for regiao, cor in cores_regioes.items()
]
ax.legend(
    handles=handles,
    title="Região",
    loc="upper left",
    bbox_to_anchor=(1.02, 1),
    frameon=False,
)

# Títulos e rótulos (em português europeu, unidade '%' estritamente)
ax.set_title(
    "Distribuição da quota de consumo em baixa tensão por distrito",
    fontsize=14,
    pad=15,
    weight="bold",
    loc="left",
)
ax.set_xlabel("Quota de baixa tensão (%)", fontsize=11, labelpad=10)
ax.set_ylabel("Distrito", fontsize=11, labelpad=10)

# Ajustes finais de estética
ax.tick_params(axis="both", which="major", labelsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.grid(axis="x", linestyle="--", alpha=0.7)

# Garantir que tudo cabe perfeitamente
plt.tight_layout()

# Gravar figura
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
