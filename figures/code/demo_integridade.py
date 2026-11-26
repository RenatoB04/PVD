# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p2_anual_nacional.csv'
OUTPUT_PATH = 'figures/demo_integridade.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import pandas as pd

# Ler os dados
df = pd.read_csv(DATA_PATH)

# Configuração da figura (tamanho aproximado 10x6)
fig, ax = plt.subplots(figsize=(10, 6))

# Cores consistentes: destacar o ano mais recente ou usar uma cor uniforme limpa
cor_barras = "#2b5c8f"
cor_destaque = "#d95f02"

# Criar lista de cores (destacar o último ano)
cores = [cor_barras if i < len(df) - 1 else cor_destaque for i in range(len(df))]

# Gráfico de barras verticais
barras = ax.bar(
    df["ano"].astype(str),
    df["total_gwh"],
    color=cores,
    width=0.55,
    edgecolor="none",
)

# Definir os limites do eixo y começando obrigatoriamente em 0 (Princípio de Wilke para gráficos de barras)
ax.set_ylim(0, df["total_gwh"].max() * 1.12)

# Rótulos dos eixos e título em português europeu
ax.set_xlabel("Ano", fontsize=11, labelpad=10)
ax.set_ylabel("Consumo anual total (GWh)", fontsize=11, labelpad=10)
ax.set_title(
    "Consumo Anual Nacional de Eletricidade (2021–2025)",
    fontsize=14,
    fontweight="bold",
    pad=15,
)

# Adicionar os valores exatos em cima de cada barra para clareza
for barra in barras:
    altura = barra.get_height()
    ax.annotate(
        f"{altura:,.1f}".replace(",", " "),
        xy=(barra.get_x() + barra.get_width() / 2, altura),
        xytext=(0, 5),  # desvio vertical em pontos
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#333333",
    )

# Formatação e limpeza visual (Wilke's principles)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#cccccc")
ax.spines["bottom"].set_color("#cccccc")
ax.tick_params(axis="both", which="both", length=0)
ax.yaxis.grid(True, linestyle="--", alpha=0.5, color="#dddddd")
ax.set_axisbelow(True)

# Gravar a figura
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
