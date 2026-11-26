# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_concelho_2025.csv'
OUTPUT_PATH = 'figures/p1f2_hist_total.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuração de estilo inspirada em Claus Wilke
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11

# Ler dados
df = pd.read_csv(DATA_PATH)

# Preparar dados: log10 do consumo total (total_gwh)
log_data = np.log10(df['total_gwh'])
mediana_orig = df['total_gwh'].median()
mediana_log = np.log10(mediana_orig)

# Criar figura
fig, ax = plt.subplots(figsize=(10, 6))

# Histograma de densidade com KDE (regra da geometria)
sns.histplot(
    log_data,
    stat='density',
    kde=True,
    bins=30,
    color='#0072B2',
    edgecolor='white',
    alpha=0.7,
    ax=ax,
    line_kws={'linewidth': 2, 'color': '#D55E00'}
)

# Linha vertical tracejada na mediana
ax.axvline(
    mediana_log,
    color='#000000',
    linestyle='--',
    linewidth=1.5,
    label=f'Mediana: {mediana_orig:.1f} GWh (log10: {mediana_log:.2f})'
)

# Rótulos e título
ax.set_title('Distribuição do consumo anual total por concelho', fontsize=14, pad=15, weight='bold', loc='left')
ax.set_xlabel('log10 do consumo (GWh)', fontsize=12, labelpad=10)
ax.set_ylabel('Densidade', fontsize=12, labelpad=10)

# Legenda totalmente FORA da área dos dados para evitar sobreposição
ax.legend(frameon=True, facecolor='white', edgecolor='none', loc='upper left', bbox_to_anchor=(1.02, 1))

# Limpeza visual (remover espinhais desnecessários)
sns.despine(top=True, right=True)

# Gravar figura (bbox_inches='tight' garante que a legenda exterior não é cortada)
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight')
plt.close()
