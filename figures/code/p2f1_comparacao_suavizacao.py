# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p2_serie_nacional.csv'
OUTPUT_PATH = 'figures/p2f1_comparacao_suavizacao.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess

# Carregar os dados
df = pd.read_csv(DATA_PATH, parse_dates=["data"])
df = df.sort_values("data").reset_index(drop=True)

# Preparar dados para os modelos
x_idx = np.arange(len(df))
y = df["total_gwh"].values
dates = df["data"]

# 1. Tendência linear (grau 1)
poly_coeffs = np.polyfit(x_idx, y, 1)
trend_linear = np.polyval(poly_coeffs, x_idx)

# 2. Média móvel centrada de 12 meses
ma_12 = df["total_gwh"].rolling(window=12, center=True).mean()

# 3. LOWESS (frac = 0.3)
lowess_result = lowess(y, x_idx, frac=0.3, return_sorted=False)

# Configurar a figura com 3 painéis lado a lado
fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharey=True)

# Título geral
fig.suptitle("Três modelos aplicados ao consumo mensal nacional", fontsize=14, y=0.98)

# Configurações comuns do eixo X (uma marca por ano)
years_locator = mdates.YearLocator()
years_fmt = mdates.DateFormatter("%Y")

# Painel 1: Tendência linear
ax1 = axes[0]
ax1.plot(dates, y, color="#BBBBBB", linewidth=1.5, zorder=1)
ax1.plot(dates, trend_linear, color="#009E73", linewidth=2.5, zorder=2)
ax1.set_title("Tendência linear", fontsize=12)
ax1.set_ylabel("Consumo mensal (GWh)", fontsize=11)
ax1.xaxis.set_major_locator(years_locator)
ax1.xaxis.set_major_formatter(years_fmt)

# Painel 2: Média móvel centrada de 12 meses
ax2 = axes[1]
ax2.plot(dates, y, color="#BBBBBB", linewidth=1.5, zorder=1)
ax2.plot(dates, ma_12, color="#0072B2", linewidth=2.5, zorder=2)
ax2.set_title("Média móvel centrada de 12 meses", fontsize=12)
ax2.xaxis.set_major_locator(years_locator)
ax2.xaxis.set_major_formatter(years_fmt)

# Painel 3: LOWESS (frac = 0,3)
ax3 = axes[2]
ax3.plot(dates, y, color="#BBBBBB", linewidth=1.5, zorder=1)
ax3.plot(dates, lowess_result, color="#D55E00", linewidth=2.5, zorder=2)
ax3.set_title("LOWESS (frac = 0,3)", fontsize=12)
ax3.xaxis.set_major_locator(years_locator)
ax3.xaxis.set_major_formatter(years_fmt)

# Ajustes finais de estética (princípios de Wilke: remover linhas de contorno desnecessárias, grelha subtil)
for ax in axes:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#CCCCCC")
    ax.tick_params(axis="x", rotation=0)

plt.tight_layout(rect=[0, 0, 1, 0.95])

# Gravar e fechar
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
