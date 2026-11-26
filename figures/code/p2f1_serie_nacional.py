# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p2_serie_nacional.csv'
OUTPUT_PATH = 'figures/p2f1_serie_nacional.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import json
import textwrap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess

# Carregar textos do JSON
texts_path = "data/clean/p2f1_texts.json"
with open(texts_path, encoding="utf-8") as f:
    texts_data = json.load(f)["serie_nacional"]

title_text = texts_data["title"]
subtitle_text = texts_data["subtitle"]
caption_text = texts_data["caption"]

# Ler o dataset
df = pd.read_csv(DATA_PATH, parse_dates=["data"])

# Configurar a figura
fig, ax = plt.subplots(figsize=(12, 7.5))

# Coordenadas x numéricas para o LOWESS
x_num = np.arange(len(df))

# 1. Série observada (linha fina cinzenta com pequenos pontos)
ax.plot(
    df["data"],
    df["total_gwh"],
    color="#999999",
    linewidth=1,
    marker="o",
    markersize=3,
    label="Observado",
)

# 2. Média móvel centrada de 12 meses
rolling_mean = df["total_gwh"].rolling(12, center=True).mean()
ax.plot(
    df["data"],
    rolling_mean,
    color="#0072B2",
    linewidth=2,
    label="Média móvel 12 meses",
)

# 3. Curva LOWESS
lowess_result = lowess(df["total_gwh"], x_num, frac=0.3, return_sorted=False)
ax.plot(
    df["data"],
    lowess_result,
    color="#D55E00",
    linewidth=2.5,
    label="LOWESS",
)

# Formatação dos eixos
ax.set_xlabel("Data", fontsize=10)
ax.set_ylabel("Consumo mensal (GWh)", fontsize=10)

# Eixo x com uma marca por ano
import matplotlib.dates as mates

ax.xaxis.set_major_locator(mates.YearLocator())
ax.xaxis.set_major_formatter(mates.DateFormatter("%Y"))

# Grelha horizontal suave
ax.grid(axis="y", linestyle="--", alpha=0.5, color="#cccccc")
ax.set_axisbelow(True)

# Remover espinhais desnecessários (estatística / Wilke style)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legenda fora da área do gráfico, por baixo
ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.12),
    ncol=3,
    frameon=False,
    fontsize=10,
)

# Adicionar Título e Subtítulo via fig.suptitle e fig.text
fig.suptitle(title_text, fontsize=14, fontweight="bold", x=0.08, ha="left")
fig.text(0.08, 0.90, subtitle_text, fontsize=10, color="#333333", ha="left")

# Adicionar Legenda/Caption no rodapé com textwrap
wrapped_caption = textwrap.fill(caption_text, width=120)
fig.text(0.08, 0.02, wrapped_caption, fontsize=9, color="#555555", ha="left")

# Ajustar layout para reservar espaço para título, subtítulo e rodapé
fig.subplots_adjust(top=0.86, bottom=0.22, left=0.08, right=0.95)

# Guardar figura e fechar
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
