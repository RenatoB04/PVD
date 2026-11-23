# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_distrito_variacao.csv'
OUTPUT_PATH = 'figures/p1f1_divergente_variacao.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# Ler os dados
df = pd.read_csv(DATA_PATH)

# Calcular a variação percentual e ordenar
df = df.sort_values('var_pct', ascending=True)

# Calcular limites simétricos para a normalização
m = df['var_pct'].abs().max()
norm = mcolors.TwoSlopeNorm(vcenter=0, vmin=-m, vmax=m)
cmap = plt.get_cmap('PuOr')

# Configuração da figura
fig, ax = plt.subplots(figsize=(10, 6))

# Criar barras horizontais
bars = ax.barh(df['distrito'], df['var_pct'], color=cmap(norm(df['var_pct'])), edgecolor='white', height=0.7)

# Linha vertical em 0
ax.axvline(0, color='black', linestyle='--', linewidth=0.8)

# Rótulos e limites
ax.set_xlabel('Variação percentual (%)')
ax.set_ylabel('Distrito')
ax.set_title('Variação do consumo de energia por distrito (2022-2025)')
ax.set_xlim(-m * 1.25, m * 1.25)

# Adicionar valores nas barras
for bar in bars:
    width = bar.get_width()
    label_x = width + (m * 0.05 if width >= 0 else -m * 0.05)
    ha = 'left' if width >= 0 else 'right'
    ax.text(label_x, bar.get_y() + bar.get_height()/2, f'{width:.1f}%', 
            va='center', ha=ha, fontsize=9)

# Barra de cor (colorbar)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.05)
cbar.set_label('Variação (%)')

# Estética limpa
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()

# Gravar e fechar
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
