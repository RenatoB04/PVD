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

# 1. Carregar dados e textos
df = pd.read_csv(DATA_PATH)
d = df[(df['bt_gwh'] > 0) & (df['mt_gwh'] > 0)].copy()

texts_path = 'data/clean/p2f1_texts.json'
with open(texts_path, encoding='utf-8') as f:
    T = json.load(f)['scatter']

# 2. Configuração da figura e layout (Wilke style: limpo, sem moldura superior/direita)
fig, ax = plt.subplots(figsize=(11, 9))

# Espaço reservado para título, subtítulo e rodapé
fig.subplots_adjust(top=0.85, bottom=0.18, left=0.08, right=0.80)

# Título e subtítulo (Wilke: sem maiúsculas excessivas, alinhados à esquerda)
fig.suptitle(T['title'], fontsize=14, fontweight='bold', x=0.08, ha='left')
fig.text(0.08, 0.89, T['subtitle'], fontsize=10, color='#555555', ha='left')

# 3. Cores e regiões (Paleta ColorBrewer / Okabe-Ito amigável a daltónicos)
cores = {
    'Norte': '#0072B2',
    'Centro': '#E69F00',
    'Lisboa e Vale do Tejo': '#D55E00',
    'Alentejo': '#009E73',
    'Algarve': '#CC79A7'
}

for regiao, cor in cores.items():
    subset = d[d['regiao'] == regiao]
    ax.scatter(
        subset['bt_gwh'],
        subset['mt_gwh'],
        s=35,
        alpha=0.75,
        c=cor,
        label=regiao,
        edgecolors='none'
    )

# 4. Escalas logarítmicas
ax.set_xscale('log')
ax.set_yscale('log')

# 5. Reta de regressão em log-log
log_bt = np.log10(d['bt_gwh'])
log_mt = np.log10(d['mt_gwh'])
a, b = np.polyfit(log_bt, log_mt, 1)

x_vals = np.array([d['bt_gwh'].min(), d['bt_gwh'].max()])
y_vals = 10**(a * np.log10(x_vals) + b)
ax.plot(x_vals, y_vals, linestyle='--', color='#333333', linewidth=1.5, label='Regressão log-log')

# 6. Caixa de texto com estatísticas (canto superior esquerdo)
stats = T['stats']
texto_stats = (
    f"r (Pearson log-log): {stats['r_pearson_log']:.2f}\n"
    f"ρ (Spearman): {stats['rho_spearman']:.2f}\n"
    f"n: {stats['n_concelhos']}"
)

ax.text(
    0.03, 0.95,
    texto_stats,
    transform=ax.transAxes,
    fontsize=9,
    verticalalignment='top',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8, edgecolor='#cccccc')
)

# 7. Eixos e grelha subtil
ax.set_xlabel('Consumo BT (GWh)', fontsize=10)
ax.set_ylabel('Consumo MT/AT/MAT (GWh)', fontsize=10)

ax.grid(True, which='both', linestyle=':', linewidth=0.5, color='#dddddd')
ax.set_axisbelow(True)

# Remover espinhas superiores e direitas (Wilke)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#333333')
ax.spines['bottom'].set_color('#333333')

# 8. Legenda fora do gráfico (à direita)
ax.legend(
    title='Região',
    bbox_to_anchor=(1.05, 1),
    loc='upper left',
    frameon=False,
    fontsize=9,
    title_fontsize=10
)

# 9. Legenda / Nota de rodapé explicativa
caption_wrapped = textwrap.fill(T['caption'], width=120)
fig.text(0.08, 0.04, caption_wrapped, fontsize=9, color='#333333', ha='left', va='top', wrap=True)

# 10. Gravar e fechar
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight')
plt.close()
