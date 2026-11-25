# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_concelho_2025.csv'
OUTPUT_PATH = 'figures/p1f2_dist_distrito.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from matplotlib.patches import Patch

# Configuração de estilo inspirada em Claus Wilke
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 11

# Ler dados
df = pd.read_csv(DATA_PATH)

# Calcular a mediana da quota_bt_pct por distrito para ordenar os grupos
ordem_distritos = (
    df.groupby('distrito')['quota_bt_pct']
    .median()
    .sort_values(ascending=True)  # Ordem ascendente para o eixo horizontal (mais baixo em baixo)
    .index
)

# Paleta de cores baseada na região
palette_regiao = {
    'Norte': '#0072B2',
    'Centro': '#E69F00',
    'Lisboa e Vale do Tejo': '#D55E00',
    'Alentejo': '#009E73',
    'Algarve': '#CC79A7'
}

# Mapear a cor predominante de cada distrito com base na sua região mais frequente
map_distrito_regiao = df.groupby('distrito')['regiao'].agg(lambda x: x.mode()[0]).to_dict()
palette_distritos = {dist: palette_regiao[map_distrito_regiao[dist]] for dist in ordem_distritos}

# Criar a figura (como há mais de 8 grupos, usamos orientação horizontal)
fig, ax = plt.subplots(figsize=(10, 8))

# Boxplot horizontal
sns.boxplot(
    data=df,
    y='distrito',
    x='quota_bt_pct',
    order=ordem_distritos,
    palette=palette_distritos,
    ax=ax,
    fliersize=0,  # Ocultar outliers do boxplot para não duplicar com o stripplot
    boxprops=dict(alpha=0.7),
    linewidth=1.2
)

# Pontos individuais sobrepostos (stripplot)
sns.stripplot(
    data=df,
    y='distrito',
    x='quota_bt_pct',
    order=ordem_distritos,
    color='black',
    alpha=0.4,
    jitter=0.2,
    size=5,
    ax=ax
)

# Remover molduras desnecessárias (despine)
sns.despine(ax=ax, top=True, right=True, left=False, bottom=False)

# Rótulos e títulos limpos e informativos
ax.set_title('Distribuição da quota de consumo em baixa tensão por distrito', fontsize=14, pad=15, loc='left', fontweight='bold')
ax.set_xlabel('Quota de Baixa Tensão [% (GWh)]', fontsize=11, labelpad=10)
ax.set_ylabel('Distrito', fontsize=11, labelpad=10)

# Ajustar limites e grelha
ax.set_xlim(0, 101)
ax.xaxis.grid(True, linestyle='--', alpha=0.5)
ax.yaxis.grid(False)

# Legenda manual para as regiões
legend_elements = [Patch(facecolor=color, label=regiao) for regiao, color in palette_regiao.items()]
ax.legend(handles=legend_elements, title='Região', loc='lower right', frameon=True, facecolor='white', framealpha=0.9)

# Guardar figura
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight')
plt.close()
