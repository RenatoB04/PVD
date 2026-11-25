# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/f2_distrito.csv'
OUTPUT_PATH = 'figures/p1f2_treemap.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import squarify

# Ler os dados
df = pd.read_csv(DATA_PATH)

# Agrupar e calcular totais por região e distrito
df_regiao = df.groupby('regiao')['total_gwh'].sum().reset_index()
df_regiao = df_regiao.sort_values(by='total_gwh', ascending=False).reset_index(drop=True)

# Cores especificadas para as regiões
cores_regiao = {
    'Norte': '#0072B2',
    'Centro': '#E69F00',
    'Lisboa e Vale do Tejo': '#D55E00',
    'Alentejo': '#009E73',
    'Algarve': '#CC79A7'
}

fig, ax = plt.subplots(figsize=(10, 6))

W, H = 100.0, 100.0

# Normalizar e calcular retângulos para as regiões
totais_regiao = df_regiao['total_gwh'].tolist()
rects_reg = squarify.squarify(squarify.normalize_sizes(totais_regiao, W, H), 0, 0, W, H)

# Iterar sobre cada região para desenhar o nível 2 (distritos)
for i, r in enumerate(rects_reg):
    reg_nome = df_regiao.loc[i, 'regiao']
    cor_base = cores_regiao.get(reg_nome, '#999999')
    
    # Desenhar contorno grosso da região
    reg_patch = mpatches.Rectangle(
        (r['x'], r['y']), r['dx'], r['dy'],
        linewidth=2, edgecolor='white', facecolor='none', zorder=3
    )
    ax.add_patch(reg_patch)
    
    # Filtrar distritos da região e ordenar por valor decrescente
    df_dist = df[df['regiao'] == reg_nome].sort_values(by='total_gwh', ascending=False).reset_index(drop=True)
    
    valores_dist = df_dist['total_gwh'].tolist()
    if sum(valores_dist) > 0:
        norm_dist = squarify.normalize_sizes(valores_dist, r['dx'], r['dy'])
        rects_dist = squarify.squarify(norm_dist, r['x'], r['y'], r['dx'], r['dy'])
        
        for j, rd in enumerate(rects_dist):
            dist_nome = df_dist.loc[j, 'distrito']
            val = df_dist.loc[j, 'total_gwh']
            
            # Retângulo do distrito
            dist_patch = mpatches.Rectangle(
                (rd['x'], rd['y']), rd['dx'], rd['dy'],
                linewidth=0.8, edgecolor='white', facecolor=cor_base, alpha=0.85, zorder=2
            )
            ax.add_patch(dist_patch)
            
            # Etiqueta dentro do retângulo se houver espaço suficiente
            if rd['dx'] > 8 and rd['dy'] > 8:
                texto = f"{dist_nome}\n{val:.0f} GWh"
                ax.text(
                    rd['x'] + rd['dx'] / 2, rd['y'] + rd['dy'] / 2,
                    texto, color='white', weight='bold', fontsize=8,
                    ha='center', va='center', zorder=4
                )

# Configurações finais do gráfico
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_axis_off()

# Criar legenda para as regiões usando mpatches corretamente
patches_legenda = [
    mpatches.Patch(color=cor, label=reg) 
    for reg, cor in cores_regiao.items() if reg in df_regiao['regiao'].values
]
ax.legend(handles=patches_legenda, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=len(patches_legenda), frameon=False)

plt.title("Consumo de eletricidade por região e distrito (2025)", fontsize=14, weight='bold', pad=15)

plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
