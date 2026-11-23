# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_concelho_2025.csv'
OUTPUT_PATH = 'figures/p1f1_scatter_escalas.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv(DATA_PATH)

cores = {
    'Norte': '#0072B2',
    'Centro': '#E69F00',
    'Lisboa e Vale do Tejo': '#D55E00',
    'Alentejo': '#009E73',
    'Algarve': '#CC79A7'
}
formas = {'Predomínio BT': 'o', 'Predomínio MT/AT/MAT': '^'}

top3 = df.nlargest(3, 'total_gwh')

fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.subplots_adjust(right=0.78)

for i, ax in enumerate(axes):
    is_log = (i == 1)
    if is_log:
        df_plot = df[df['mt_gwh'] > 0].copy()
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_title('Escala logarítmica')
        n_excluidos = len(df) - len(df_plot)
        ax.text(0.05, 0.95, f'Excluídos (MT=0): {n_excluidos}', transform=ax.transAxes, va='top')
    else:
        df_plot = df
        ax.set_title('Escala linear')

    for reg, cor in cores.items():
        for perf, form in formas.items():
            subset = df_plot[(df_plot['regiao'] == reg) & (df_plot['perfil'] == perf)]
            ax.scatter(subset['bt_gwh'], subset['mt_gwh'], s=subset['total_gwh'] * 0.5, 
                       c=cor, marker=form, alpha=0.7, edgecolors='white', linewidth=0.5)

    for _, row in top3.iterrows():
        if is_log and row['mt_gwh'] == 0: continue
        ax.annotate(row['concelho'], xy=(row['bt_gwh'], row['mt_gwh']), 
                    xytext=(10, 10), textcoords='offset points', fontsize=8,
                    arrowprops=dict(arrowstyle='->', color='black', lw=0.5))

    ax.set_xlabel('Consumo BT (GWh)')
    ax.set_ylabel('Consumo MT/AT/MAT (GWh)')
    ax.grid(True, linestyle='--', alpha=0.3)

# Legendas
handles_reg = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=10) for c in cores.values()]
leg1 = fig.legend(handles_reg, cores.keys(), title='Região', bbox_to_anchor=(0.95, 0.85), frameon=False)

handles_perf = [plt.Line2D([0], [0], marker=f, color='w', markerfacecolor='gray', markersize=10) for f in formas.values()]
leg2 = fig.legend(handles_perf, formas.keys(), title='Perfil', bbox_to_anchor=(0.95, 0.65), frameon=False)

sizes = [100, 500, 1000]
handles_size = [plt.scatter([], [], s=s*0.5, c='gray') for s in sizes]
leg3 = fig.legend(handles_size, [str(s) for s in sizes], title='Consumo total (GWh)', bbox_to_anchor=(0.95, 0.45), frameon=False)

fig.suptitle('Distribuição do Consumo de Energia por Concelho (2025)', fontsize=14)
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
