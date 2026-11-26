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
import pandas as pd

# Carregar textos do JSON
texts_path = "data/clean/p2f1_texts.json"
with open(texts_path, encoding="utf-8") as f:
    texts = json.load(f)

title_text = texts["regioes"]["title"]
subtitle_text = texts["regioes"]["subtitle"]
caption_text = texts["regioes"]["caption"]

# Ler dados
df = pd.read_csv(DATA_PATH, parse_dates=["data"])

# Pivotar para ter datas nas linhas e regiões nas colunas
df_pivot = df.pivot(index="data", columns="regiao", values="consumo_gwh")

# Calcular a média de 2022 para cada região e normalizar (base 100)
mean_2022 = df_pivot.loc["2022"].mean()
df_indexed = (df_pivot / mean_2022) * 100

# Suavizar com média móvel centrada de 12 meses
df_smoothed = df_indexed.rolling(12, center=True).mean()

# Definir cores exatas conforme especificação
colors = {
    "Norte": "#0072B2",
    "Centro": "#E69F00",
    "Lisboa e Vale do Tejo": "#D55E00",
    "Alentejo": "#009E73",
    "Algarve": "#CC79A7",
}

# Criar figura e eixo
fig, ax = plt.subplots(figsize=(12, 7.5))

# Plotar linhas por região
for regiao, color in colors.items():
    if regiao in df_smoothed.columns:
        ax.plot(
            df_smoothed.index,
            df_smoothed[regiao],
            label=regiao,
            linewidth=2,
            color=color,
        )

# Linha horizontal tracejada em y = 100
ax.axhline(100, color="gray", linestyle="--", linewidth=1, zorder=0)

# Eixos e rótulos
ax.set_xlabel("Data", fontsize=11)
ax.set_ylabel(
    "Índice de consumo (2022 = 100, média móvel de 12 meses)", fontsize=11
)

# Formatar eixo x com marcas anuais
import matplotlib.dates as mdates

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

# Remover elementos decorativos desnecessários (Spines superiores e direitos)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legenda fora do gráfico, à direita
ax.legend(
    loc="center left",
    bbox_to_anchor=(1.02, 0.5),
    frameon=False,
    title="Região",
    fontsize=10,
    title_fontsize=11,
)

# Ajustar layout para acomodar título, subtítulo e legenda no rodapé
fig.subplots_adjust(top=0.85, bottom=0.20, left=0.08, right=0.82)

# Adicionar Título e Subtítulo usando fig.suptitle e fig.text
fig.suptitle(title_text, fontsize=14, fontweight="bold", x=0.08, ha="left")
fig.text(
    0.08,
    0.90,
    subtitle_text,
    fontsize=10,
    color="#555555",
    ha="left",
    va="center",
)

# Adicionar legenda no rodapé com textwrap
wrapped_caption = textwrap.fill(caption_text, width=120)
fig.text(0.08, 0.04, wrapped_caption, fontsize=9, ha="left", va="top")

# Guardar figura
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
