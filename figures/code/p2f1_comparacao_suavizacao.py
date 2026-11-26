# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p2_serie_nacional.csv'
OUTPUT_PATH = 'figures/p2f1_comparacao_suavizacao.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess
import matplotlib.dates as mdates

# Carregar os dados
df = pd.read_csv(DATA_PATH, parse_dates=["data"])

# Preparar dados e modelos
x_idx = np.arange(len(df))
y = df["total_gwh"].values

# 1. Tendência linear (grau 1)
poly_coeffs = np.polyfit(x_idx, y, 1)
trend_linear = np.polyval(poly_coeffs, x_idx)

# 2. Média móvel centrada de 12 meses
ma_12 = df["total_gwh"].rolling(window=12, center=True).mean().values

# 3. LOWESS (frac = 0.3)
lowess_res = lowess(y, x_idx, frac=0.3, return_sorted=False)

# Configuração da figura (1 linha, 3 colunas, sharey=True)
fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharey=True)

# Título geral
fig.suptitle("Três modelos aplicados ao consumo mensal nacional", fontsize=14, fontweight="bold", y=1.02)

# Definições comuns para os painéis
models = [
    ("Tendência linear", trend_linear, "#009E73"),
    ("Média móvel centrada de 12 meses", ma_12, "#0072B2"),
    ("LOWESS (frac = 0,3)", lowess_res, "#D55E00")
]

for i, (title, model_values, color) in enumerate(models):
    ax = axes[i]
    
    # Série mensal nacional em cinzento claro
    ax.plot(df["data"], y, color="#BBBBBB", linewidth=1.5, zorder=1)
    
    # Modelo sobreposto
    ax.plot(df["data"], model_values, color=color, linewidth=2.5, zorder=2)
    
    # Título do painel
    ax.set_title(title, fontsize=12)
    
    # Formatação do eixo das x (uma marca por ano)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    
    # Rótulo do eixo y apenas no primeiro painel
    if i == 0:
        ax.set_ylabel("Consumo mensal (GWh)", fontsize=11)
        
    # Limpeza visual (remover espinhais desnecessários)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

# Ajustar espaçamento
plt.tight_layout()

# Gravar e fechar
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
