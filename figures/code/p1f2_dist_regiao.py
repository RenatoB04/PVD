# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_concelho_2025.csv'
OUTPUT_PATH = 'figures/p1f2_dist_regiao.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ler os dados
df = pd.read_csv(DATA_PATH)

# Definir a paleta de cores exata solicitada
palette = {
    "Norte": "#0072B2",
    "Centro": "#E69F00",
    "Lisboa e Vale do Tejo": "#D55E00",
    "Alentejo": "#009E73",
    "Algarve": "#CC79A7"
}

# Calcular a mediana por região para ordenar os grupos (ordem decrescente)
median_order = (
    df.groupby("regiao")["quota_bt_pct"]
    .median()
    .sort_values(ascending=False)
    .index
)

# Configurar a figura
fig, ax = plt.subplots(figsize=(10, 6))

# Estilo visual limpo (Wilke style)
sns.set_theme(style="white")

# Boxplot com os grupos ordenados pela mediana
sns.boxplot(
    data=df,
    x="quota_bt_pct",
    y="regiao",
    order=median_order,
    palette=palette,
    ax=ax,
    boxprops=dict(alpha=0.6),
    linewidth=1.2,
    fliersize=0  # Remover os outliers predefinidos para evitar duplicação com o stripplot
)

# Sobrepor os pontos individuais (stripplot) com jitter e semitransparência
sns.stripplot(
    data=df,
    x="quota_bt_pct",
    y="regiao",
    order=median_order,
    color="black",
    alpha=0.5,
    jitter=0.2,
    size=5,
    ax=ax
)

# Rótulos e título em português europeu com unidade solicitada (GWh)
ax.set_title("Distribuição da quota de consumo em baixa tensão por região", fontsize=14, pad=15, loc="left", fontweight="bold")
ax.set_xlabel("Quota de baixa tensão (GWh)", fontsize=11)
ax.set_ylabel("Região", fontsize=11)

# Remover molduras desnecessárias (despine)
sns.despine(top=True, right=True)

# Ajustar limites do eixo x (0 a 100%)
ax.set_xlim(0, 100)

# Guardar a figura
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
