# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/f2_regiao.csv'
OUTPUT_PATH = 'figures/p1f2_regiao.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import pandas as pd

# Ler os dados
df = pd.read_csv(DATA_PATH)

# Ordenar os dados da menor para a maior para que a maior fique no topo no barh
df = df.sort_values(by="total_gwh", ascending=True)

# Configuração da figura (Wilke: proporção adequada, limpa)
fig, ax = plt.subplots(figsize=(10, 6))

# Cores específicas pedidas no enunciado
cores_regioes = {
    "Norte": "#0072B2",
    "Centro": "#E69F00",
    "Lisboa e Vale do Tejo": "#D55E00",
    "Alentejo": "#009E73",
    "Algarve": "#CC79A7",
}
bar_colors = [cores_regioes.get(reg, "#0072B2") for reg in df["regiao"]]

# Criar o gráfico de barras horizontais
bars = ax.barh(df["regiao"], df["total_gwh"], color=bar_colors, height=0.6)

# Garantir que o eixo X comece em zero
ax.set_xlim(0, df["total_gwh"].max() * 1.15)

# Adicionar os valores junto a cada barra
for bar in bars:
    width = bar.get_width()
    ax.text(
        width + (df["total_gwh"].max() * 0.01),
        bar.get_y() + bar.get_height() / 2,
        f"{width:.1f} GWh",
        va="center",
        ha="left",
        fontsize=10,
        color="#333333",
    )

# Títulos e rótulos (Português Europeu, unidades incluídas)
ax.set_title(
    "Consumo total de eletricidade por região em 2025",
    fontsize=14,
    pad=15,
    fontweight="bold",
)
ax.set_xlabel("Consumo total (GWh)", fontsize=11, labelpad=10)
ax.set_ylabel("Região", fontsize=11, labelpad=10)

# Limpeza do design (remover bordas desnecessárias, Wilke principle)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#CCCCCC")
ax.spines["bottom"].set_color("#CCCCCC")

ax.xaxis.grid(True, linestyle="--", alpha=0.5, color="#CCCCCC")
ax.set_axisbelow(True)

# Ajustar margens
plt.tight_layout()

# Guardar figura
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
