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

# Carregar dados
df = pd.read_csv(DATA_PATH)

# Filtrar concelhos com mt_gwh > 0
df_filtered = df[(df['mt_gwh'] > 0) & (df['bt_gwh'] > 0)].copy()

# Carregar textos e estatísticas do JSON utilizando DATA_PATH para derivar o caminho correto
texts_path = DATA_PATH.replace('p2f1_data.csv', 'p2f1_texts.json')
with open(texts_path, encoding='utf-8') as f:
    json_data = json.load(f)

texts = json_data['scatter']
stats = json_data['stats']

# Ler valores estatísticos diretamente do JSON conforme solicitado
r_val = stats['r_pearson_log']
rho_val = stats['rho_spearman']
n_val = stats['n_concelhos']

# Configuração da figura (Wilke style: limpa, sem elementos decorativos desnecessários)
fig, ax = plt.subplots(figsize=(11, 9))

# Cores exatas solicitadas
colors = {
    'Norte': '#0072B2',
    'Centro': '#E69F00',
    'Lisboa e Vale do Tejo': '#D55E00',
    'Alentejo': '#009E73',
    'Algarve': '#CC79A7'
}

# Scatter plot por região
for regiao, color in colors.items():
    subset = df_filtered[df_filtered['regiao'] == regiao]
    if not subset.empty:
        ax.scatter(
            subset['bt_gwh'], 
            subset['mt_gwh'], 
            s=35, 
            alpha=0.75, 
            color=color, 
            label=regiao
        )

# Escala logarítmica
ax.set_xscale('log')
ax.set_yscale('log')

# Reta de regressão em log-log: np.polyfit(np.log10(x), np.log10(y), 1)
log_x = np.log10(df_filtered['bt_gwh'])
log_y = np.log10(df_filtered['mt_gwh'])
b, a = np.polyfit(log_x, log_y, 1)

# Desenhada ao longo do intervalo de x (10**(a*log10(x)+b))
x_vals = np.sort(df_filtered['bt_gwh'])
y_vals = 10**(b * np.log10(x_vals) + a)
ax.plot(x_vals, y_vals, color='black', linestyle='--', linewidth=1.5, alpha=0.8)

# Caixa de texto no canto superior esquerdo com valores arredondados a 2 casas decimais
stats_text = f"r (log-log) = {r_val:.2f}\nρ (Spearman) = {rho_val:.2f}\nn = {n_val}"
ax.text(
    0.03, 0.97, stats_text,
    transform=ax.transAxes,
    fontsize=10,
    verticalalignment='top',
    bbox=dict(boxstyle='square,pad=0.5', facecolor='white', edgecolor='0.8', alpha=0.9)
)

# Eixos
ax.set_xlabel('Consumo BT (GWh)', fontsize=11)
ax.set_ylabel('Consumo MT/AT/MAT (GWh)', fontsize=11)

# Remover moldura superior e direita (clean plot)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(top=False, right=False)

# Legenda fora do gráfico à direita
ax.legend(
    title='Região',
    bbox_to_anchor=(1.02, 1),
    loc='upper left',
    frameon=False,
    fontsize=10,
    title_fontsize=11
)

# Títulos, subtítulos e legenda via texto estruturado com reserva de espaço
fig.suptitle(texts['title'], fontsize=14, fontweight='bold', x=0.01, ha='left')
fig.text(0.01, 0.89, texts['subtitle'], fontsize=10, color='0.3', ha='left')

wrapped_caption = textwrap.fill(texts['caption'], width=120)
fig.text(0.01, 0.02, wrapped_caption, fontsize=9, color='0.3', ha='left', va='bottom', wrap=True)

# Ajuste de layout para acomodar título, subtítulo e rodapé
fig.subplots_adjust(left=0.08, right=0.80, top=0.87, bottom=0.12)

plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight')
plt.close()
