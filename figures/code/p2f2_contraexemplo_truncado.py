# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p2_anual_nacional.csv'
OUTPUT_PATH = 'figures/p2f2_contraexemplo_truncado.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import pandas as pd

# Ler os dados
df = pd.read_csv(DATA_PATH)

anos = df["ano"]
total = df["total_gwh"]

# Calcular razões reais e visuais
val_max = total.max()
val_min = total.min()
razao_real = val_max / val_min

# Configuração da figura com 2 painéis
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.5))

cor_barra = "#0072B2"

# -------------------------------------------------------------
# Painel Esquerdo: Eixo truncado
# -------------------------------------------------------------
ymin_1 = 0.97 * val_min
ymax_1 = 1.01 * val_max

ax1.bar(anos, total, color=cor_barra, width=0.6, zorder=3)
ax1.set_ylim(ymin_1, ymax_1)
ax1.set_title(
    "Contraexemplo: eixo truncado (distorce as magnitudes)",
    fontsize=11,
    pad=10,
    fontweight="bold",
)
ax1.set_ylabel("Consumo anual (GWh)", fontsize=10)
ax1.set_xlabel("Ano", fontsize=10)
ax1.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)

razao_visual_1 = (val_max - ymin_1) / (val_min - ymin_1)
texto_1 = (
    f"Razão real: {razao_real:.2f}x\n"
    f"Razão visual: {razao_visual_1:.2f}x".replace(".", ",")
)
ax1.text(
    0.05,
    0.92,
    texto_1,
    transform=ax1.transAxes,
    fontsize=10,
    verticalalignment="top",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9, edgecolor="#CCCCCC"),
)

# -------------------------------------------------------------
# Painel Direito: Eixo a partir de zero
# -------------------------------------------------------------
ymin_2 = 0
ymax_2 = val_max * 1.15

ax2.bar(anos, total, color=cor_barra, width=0.6, zorder=3)
ax2.set_ylim(ymin_2, ymax_2)
ax2.set_title(
    "Correto: eixo a partir de zero", fontsize=11, pad=10, fontweight="bold"
)
ax2.set_ylabel("Consumo anual (GWh)", fontsize=10)
ax2.set_xlabel("Ano", fontsize=10)
ax2.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)

razao_visual_2 = (val_max - ymin_2) / (val_min - ymin_2)
texto_2 = (
    f"Razão real: {razao_real:.2f}x\n"
    f"Razão visual: {razao_visual_2:.2f}x".replace(".", ",")
)
ax2.text(
    0.05,
    0.92,
    texto_2,
    transform=ax2.transAxes,
    fontsize=10,
    verticalalignment="top",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9, edgecolor="#CCCCCC"),
)

# Título geral
fig.suptitle(
    "Princípio da tinta proporcional: a altura da barra tem de ser proporcional ao valor",
    fontsize=13,
    fontweight="bold",
    y=0.98,
)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
