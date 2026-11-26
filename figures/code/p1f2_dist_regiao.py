# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_concelho_2025.csv'
OUTPUT_PATH = 'figures/p1f2_dist_regiao.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Carregar os dados
df = pd.read_csv(DATA_PATH)

# Definir a paleta de cores estipulada
palette = {
    "Norte": "#0072B2",
    "Centro": "#E69F00",
    "Lisboa e Vale do Tejo": "#D55E00",
    "Alentejo": "#009E73",
    "Algarve": "#CC79A7"
}

# Calcular a ordem das regiões com base na mediana da quota_bt_pct
order = df.groupby("regiao")["quota_bt_pct"].median().sort_values(ascending=False).index

# Configuração da figura (Wilke: proporção adequada, limpa)
fig, ax = plt.subplots(figsize=(10, 6))

# Boxplot com os grupos ordenados pela mediana
sns.boxplot(
    data=df,
    x="quota_bt_pct",
    y="regiao",
    order=order,
    palette=palette,
    ax=ax,
    boxprops=dict(alpha=0.7),
    showfliers=False,  # Evitar duplicação de outliers com o stripplot
    width=0.5
)

# Pontos individuais sobrepostos com jitter para mostrar a distribuição completa
sns.stripplot(
    data=df,
    x="quota_bt_pct",
    y="regiao",
    order=order,
    color="black",
    alpha=0.4,
    size=5,
    jitter=0.2,
    ax=ax
)

# Rótulos e título claros em português europeu
ax.set_title("Distribuição da quota de consumo em baixa tensão por região (2025)", fontsize=13, pad=15, weight='bold')
ax.set_xlabel("Quota de baixa tensão (%)", fontsize=11)
ax.set_ylabel("", fontsize=11)

# Remover decorações desnecessárias (top e right spines)
sns.despine(top=True, right=True, left=False, bottom=False)

# Garantir limites adequados para o eixo X
ax.set_xlim(0, 105)

# Ajustar layout para evitar cortes
plt.tight_layout()

# Guardar figura e fechar
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
