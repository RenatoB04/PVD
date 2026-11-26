# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p2_concelho_mes_bt_mt.csv'
OUTPUT_PATH = 'figures/p2f2_sobreposicao.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Ler os dados
df = pd.read_csv(DATA_PATH, parse_dates=["data"])

# Filtrar e calcular contagens
total_linhas = len(df)
df_valid = df[(df["bt_gwh"] > 0) & (df["mt_gwh"] > 0)].copy()
n_usadas = len(df_valid)
n_excluidas = total_linhas - n_usadas

# Configurar a figura com 3 painéis lado a lado
fig, axes = plt.subplots(1, 3, figsize=(18, 6.2), sharex=True, sharey=True)

# Coordenadas e dados
x = df_valid["bt_gwh"]
y = df_valid["mt_gwh"]

# Painel 1: Pontos opacos (sobreposição)
ax1 = axes[0]
ax1.scatter(x, y, s=10, alpha=1.0, color="#0072B2", linewidths=0)
ax1.set_title("Pontos opacos (sobreposição)", fontsize=12)
ax1.set_xscale("log")
ax1.set_yscale("log")
ax1.set_xlabel("Consumo BT (GWh)", fontsize=11)
ax1.set_ylabel("Consumo MT/AT/MAT (GWh)", fontsize=11)

# Painel 2: Pontos transparentes
ax2 = axes[1]
ax2.scatter(x, y, s=10, alpha=0.08, color="#0072B2", linewidths=0)
ax2.set_title("Pontos transparentes", fontsize=12)
ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_xlabel("Consumo BT (GWh)", fontsize=11)

# Painel 3: Hexbin (contagem por célula)
ax3 = axes[2]
hb = ax3.hexbin(
    x,
    y,
    gridsize=55,
    xscale="log",
    yscale="log",
    bins="log",
    mincnt=1,
    cmap="viridis",
)
ax3.set_title("Hexbin (contagem por célula)", fontsize=12)
ax3.set_xscale("log")
ax3.set_yscale("log")
ax3.set_xlabel("Consumo BT (GWh)", fontsize=11)

# Adicionar barra de cor para o hexbin fora do gráfico
cb = fig.colorbar(hb, ax=ax3, fraction=0.046, pad=0.04)
cb.set_label("Nº de observações (escala log)", fontsize=10)

# Remover elementos decorativos excessivos (espinhas desnecessárias)
for ax in axes:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

# Título geral em 2 linhas
titulo_linha1 = "Tratamento de sobreposição de pontos (Wilke, cap. 18)"
titulo_linha2 = (
    f"n = {n_usadas:,} observações concelho-mês usadas; "
    f"{n_excluidas:,} excluídas (consumo nulo)"
).replace(",", ".")

fig.suptitle(f"{titulo_linha1}\n{titulo_linha2}", fontsize=14, y=0.98)

# Ajustar layout para evitar sobreposições
plt.tight_layout()

# Gravar a figura
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
