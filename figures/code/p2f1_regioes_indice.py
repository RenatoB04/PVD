# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p2_serie_regiao.csv'
OUTPUT_PATH = 'figures/p2f1_regioes_indice.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import json
import textwrap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Carregar textos e estatísticas
with open("data/clean/p2f1_texts.json", encoding="utf-8") as f:
    texts_data = json.load(f)

T = texts_data["regioes"]
title_text = T["title"]
subtitle_text = T["subtitle"]
caption_text = textwrap.fill(T["caption"], width=120)

# Ler dados
df = pd.read_csv(DATA_PATH, parse_dates=["data"])

# Pivotar a tabela: linhas = data, colunas = regiao, valores = consumo_gwh
df_pivot = df.pivot(index="data", columns="regiao", values="consumo_gwh")

# Filtrar o ano de 2022 para calcular a média de base (2022 = 100)
mask_2022 = (df_pivot.index.year == 2022)
mean_2022 = df_pivot.loc[mask_2022].mean()

# Dividir pela média de 2022 e multiplicar por 100
df_index = (df_pivot / mean_2022) * 100

# Suavizar com média móvel centrada de 12 meses
df_smooth = df_index.rolling(window=12, center=True).mean()

# Configuração de cores, estilos de linha e marcadores solicitados
style_config = {
    "Norte": {"color": "#0072B2", "linestyle": "-", "marker": "o"},
    "Centro": {"color": "#E69F00", "linestyle": "--", "marker": "s"},
    "Lisboa e Vale do Tejo": {"color": "#D55E00", "linestyle": "-.", "marker": "^"},
    "Alentejo": {"color": "#009E73", "linestyle": ":", "marker": "D"},
    "Algarve": {"color": "#CC79A7", "linestyle": (0, (5, 1)), "marker": "v"}
}

# Criar a figura
fig, ax = plt.subplots(figsize=(12, 7.5))

# Linha horizontal tracejada cinzenta em y = 100
ax.axhline(100, color="grey", linestyle="--", linewidth=1, zorder=1)

# Desenhar cada região
for regiao, cfg in style_config.items():
    if regiao in df_smooth.columns:
        ax.plot(
            df_smooth.index,
            df_smooth[regiao],
            label=regiao,
            color=cfg["color"],
            linestyle=cfg["linestyle"],
            marker=cfg["marker"],
            markevery=6,
            markersize=6,
            linewidth=2,
            zorder=2
        )

# Rótulos dos eixos e formatação
ax.set_xlabel("Data", fontsize=10)
ax.set_ylabel("Índice de consumo (2022 = 100, média móvel de 12 meses)", fontsize=10)

# Eixo x com uma marca por ano
import matplotlib.dates as mdates
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

# Limpeza visual (estilo Wilke: remover top e right spines)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legenda fora do gráfico, à direita
ax.legend(
    title="Região",
    loc="center left",
    bbox_to_anchor=(1.02, 0.5),
    frameon=False,
    fontsize=9,
    title_fontsize=10
)

# Ajuste de layout para acomodar Título, Subtítulo e Legenda no rodapé
fig.subplots_adjust(top=0.85, bottom=0.18, left=0.08, right=0.82)

# Adicionar Título Principal
fig.suptitle(
    title_text,
    fontsize=14,
    fontweight="bold",
    x=0.08,
    ha="left",
    y=0.94
)

# Adicionar Subtítulo
fig.text(
    0.08,
    0.89,
    subtitle_text,
    fontsize=10,
    color="#555555",
    ha="left"
)

# Adicionar Legenda / Texto explicativo no rodapé
fig.text(
    0.08,
    0.02,
    caption_text,
    fontsize=9,
    ha="left",
    va="bottom",
    color="#333333"
)

# Gravar figura
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
