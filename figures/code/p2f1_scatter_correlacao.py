# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_concelho_2025.csv'
OUTPUT_PATH = 'figures/p2f1_scatter_correlacao.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import json
import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Carregar textos e estatísticas
T = json.load(open('data/clean/p2f1_texts.json', encoding='utf-8'))['scatter']
stats = T['stats']

# Ler dados
df = pd.read_csv(DATA_PATH)
d = df[(df['bt_gwh'] > 0) & (df['mt_gwh'] > 0)].copy()

# Configuração da figura
fig, ax = plt.subplots(figsize=(11, 9))

# Cores e marcadores por região
cores = {
    'Norte': '#0072B2',
    'Centro': '#E69F00',
    'Lisboa e Vale do Tejo': '#D55E00',
    'Alentejo': '#009E73',
    'Algarve': '#CC79A7'
}

marcadores = {
    'Norte': 'o',
    'Centro': 's',
    'Lisboa e Vale do Tejo': '^',
    'Alentejo': 'D',
    'Algarve': 'v'
}

# Scatter por região
for regiao, cor in cores.items():
    subset = d[d['regiao'] == regiao]
    if not subset.empty:
        ax.scatter(
            subset['bt_gwh'],
            subset['mt_gwh'],
            c=cor,
            marker=marcadores[regiao],
            s=35,
            alpha=0.75,
            edgecolors='white',
            linewidths=0.5,
            label=regiao
        )

# Regressão linear em log-log
log_bt = np.log10(d['bt_gwh'])
log_mt = np.log10(d['mt_gwh'])
a, b = np.polyfit(log_bt, log_mt, 1)

x_vals = np.array([d['bt_gwh'].min(), d['bt_gwh'].max()])
y_vals = 10**(a * np.log10(x_vals) + b)
ax.plot(x_vals, y_vals, color='black', linestyle='--', linewidth=1.5, label='Regressão log-log')

# Escalas logarítmicas
ax.set_xscale('log')
ax.set_yscale('log')

# Eixos
ax.set_xlabel('Consumo BT (GWh)', fontsize=11)
ax.set_ylabel('Consumo MT/AT/MAT (GWh)', fontsize=11)

# Caixa de texto com estatísticas
r_pearson = stats.get('r_pearson_log', 0)
rho_spearman = stats.get('rho_spearman', 0)
n_concelhos = stats.get('n_concelhos', len(d))

texto_stats = (
    f"r (Pearson log-log): {r_pearson:.2f}\n"
    f"ρ (Spearman): {rho_spearman:.2f}\n"
    f"n = {n_concelhos}"
)

props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8, edgecolor='#cccccc')
ax.text(
    0.03, 0.97,
    texto_stats,
    transform=ax.transAxes,
    fontsize=10,
    verticalalignment='top',
    bbox=props
)

# Legenda fora do gráfico
ax.legend(
    title='Região',
    bbox_to_anchor=(1.05, 1),
    loc='upper left',
    frameon=False,
    fontsize=10,
    title_fontsize=10
)

# Títulos, subtítulo e rodapé (legenda explicativa)
fig.suptitle(T['title'], fontsize=14, fontweight='bold', x=0.01, ha='left')
fig.text(0.01, 0.915, T['subtitle'], fontsize=10, color='#333333', ha='left')

legenda_texto = textwrap.fill(T['caption'], width=120)
fig.text(0.01, 0.02, legenda_texto, fontsize=9, color='#333333', ha='left', va='bottom', wrap=True)

# Ajuste de layout para evitar sobreposições
fig.subplots_adjust(top=0.88, bottom=0.18, left=0.08, right=0.80)

# Gravar figura
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
