# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/f2_concelho_mes.csv'
OUTPUT_PATH = 'figures/p1f2_concelho_mes.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import seaborn as sns

# Ler os dados
df = pd.read_csv(DATA_PATH)

# Garantir ordem cronológica dos meses
meses_ordem = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
df["mes_nome"] = pd.Categorical(df["mes_nome"], categories=meses_ordem, ordered=True)

# Identificar os 60 concelhos com maior consumo total em 2025
concelhos_totais = df.groupby("concelho")["consumo_gwh"].sum()
top_60_concelhos = concelhos_totais.nlargest(60).index

# Filtrar o DataFrame para o top 60
df_top60 = df[df["concelho"].isin(top_60_concelhos)].copy()

# Criar a tabela pivô (linhas = concelhos ordenados por consumo total decrescente, colunas = meses)
pivot_df = df_top60.pivot_table(
    index="concelho", 
    columns="mes_nome", 
    values="consumo_gwh", 
    aggfunc="sum"
)

# Ordenar as linhas pelo valor total decrescente (maior em cima)
pivot_df = pivot_df.loc[top_60_concelhos]

# Configurar a figura
fig, ax = plt.subplots(figsize=(10, 14))

# Usar escala logarítmica (LogNorm) para o heatmap
# Substituir valores zero ou negativos por NaN para evitar erros no LogNorm
pivot_vals = pivot_df.values
pivot_vals_pos = np.where(pivot_vals > 0, pivot_vals, np.nan)
vmin = np.nanmin(pivot_vals_pos)
vmax = np.nanmax(pivot_vals_pos)

norm = mcolors.LogNorm(vmin=vmin, vmax=vmax)

# Desenhar o heatmap
im = ax.imshow(pivot_vals, cmap="viridis", norm=norm, aspect="auto")

# Configurar os eixos
ax.set_xticks(np.arange(len(meses_ordem)))
ax.set_xticklabels(meses_ordem, fontsize=9)
ax.set_yticks(np.arange(len(pivot_df.index)))
ax.set_yticklabels(pivot_df.index, fontsize=7)

# Rótulos e título
ax.set_xlabel("Mês", fontsize=10)
ax.set_ylabel("Concelho (Top 60 por consumo total)", fontsize=10)
ax.set_title("Consumo mensal de energia elétrica nos 60 concelhos com maior consumo (2025)", fontsize=11, pad=12, fontweight="bold")

# Barra de cor com indicação da escala logarítmica e unidades
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("Consumo (GWh, escala logarítmica)", fontsize=10)

# Limpeza e ajustes de estilo inspirados em Claus Wilke
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.tick_params(axis="both", which="both", length=0)

plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
