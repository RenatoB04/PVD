# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_concelho_2025.csv'
OUTPUT_PATH = 'figures/p1f2_forma_regiao.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ler dados
df = pd.read_csv(DATA_PATH)

# Calcular a mediana de quota_bt_pct por região para ordenação
ordem_regioes = (
    df.groupby("regiao")["quota_bt_pct"]
    .median()
    .sort_values(ascending=False)
    .index
)

# Paleta de cores exata solicitada
cores_regioes = {
    "Norte": "#0072B2",
    "Centro": "#E69F00",
    "Lisboa e Vale do Tejo": "#D55E00",
    "Alentejo": "#009E73",
    "Algarve": "#CC79A7",
}

# Configuração da figura
fig, ax = plt.subplots(figsize=(10, 6))

# Estilo e limpeza
sns.set_theme(style="white")

# Violin plot
sns.violinplot(
    data=df,
    x="regiao",
    y="quota_bt_pct",
    order=ordem_regioes,
    palette=cores_regioes,
    inner="quartile",
    cut=0,
    density_norm="width",
    ax=ax,
    legend=False,
)

# Rótulos e título
ax.set_title("Distribuição da quota de consumo em baixa tensão por região", fontsize=14, pad=15, loc="left", fontweight="bold")
ax.set_xlabel("Região", fontsize=12)
ax.set_ylabel("Quota de baixa tensão (%)", fontsize=12)

# Ajustar eixo Y para percentagem (0 a 100 com margem estética)
ax.set_ylim(-2, 102)

# Limpar espinha dorsal do gráfico (princípios de Wilke)
sns.despine(top=True, right=True)

# Ajustar layout para evitar cortes
plt.tight_layout()

# Guardar e fechar
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
