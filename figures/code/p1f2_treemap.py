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

# 1. Ler os dados
df = pd.read_csv(DATA_PATH)

# 2. Paleta de cores oficial para as regiões
cores_regioes = {
    'Norte': '#0072B2',
    'Centro': '#E69F00',
    'Lisboa e Vale do Tejo': '#D55E00',
    'Alentejo': '#009E73',
    'Algarve': '#CC79A7'
}

# 3. Preparar a figura (figsize aproximado 11x6 para dar espaço à legenda e anotações)
fig, ax = plt.subplots(figsize=(11, 6))

W, H = 100, 100

# Agrupar por região e ordenar decrescentemente por total_gwh
totais_regiao = df.groupby('regiao')['total_gwh'].sum().sort_values(ascending=False)
regioes_ordenadas = totais_regiao.index.tolist()

# Normalizar e calcular retângulos das regiões
norm_reg = squarify.normalize_sizes(totais_regiao.values, W, H)
rects_reg = squarify.squarify(norm_reg, 0, 0, W, H)

# Mapear retângulos das regiões por nome
regiao_rects_map = {reg: rect for reg, rect in zip(regioes_ordenadas, rects_reg)}

# Preparar dados para anotações externas (pequenos retângulos)
anotacoes_externas = []
contador_pequenos = 1

# Desenhar as regiões e os distritos
for regiao in regioes_ordenadas:
    r = regiao_rects_map[regiao]
    
    # Desenhar contorno grosso da região
    rect_regiao_patch = plt.Rectangle(
        (r['x'], r['y']), r['dx'], r['dy'],
        linewidth=2.5, edgecolor='white', facecolor='none', zorder=3
    )
    ax.add_patch(rect_regiao_patch)
    
    # Filtrar distritos da região e ordenar por valor decrescente
    df_reg = df[df['regiao'] == regiao].sort_values(by='total_gwh', ascending=False)
    
    valores_dist = df_reg['total_gwh'].values
    distritos = df_reg['distrito'].values
    
    if len(valores_dist) > 0 and sum(valores_dist) > 0:
        norm_dist = squarify.normalize_sizes(valores_dist, r['dx'], r['dy'])
        rects_dist = squarify.squarify(norm_dist, r['x'], r['y'], r['dx'], r['dy'])
        
        for d_nome, val, rd in zip(distritos, valores_dist, rects_dist):
            area = rd['dx'] * rd['dy']
            cor = cores_regioes.get(regiao, '#999999')
            
            # Retângulo do distrito
            rect_dist_patch = plt.Rectangle(
                (rd['x'], rd['y']), rd['dx'], rd['dy'],
                linewidth=0.8, edgecolor='white', facecolor=cor, zorder=1
            )
            ax.add_patch(rect_dist_patch)
            
            # Decisão de rotulagem baseada na área
            cx = rd['x'] + rd['dx'] / 2
            cy = rd['y'] + rd['dy'] / 2
            
            if area >= 200:
                # Escrever nome e valor dentro do retângulo
                texto = f"{d_nome}\n{val:.0f} GWh"
                ax.text(
                    cx, cy, texto,
                    ha='center', va='center', fontsize=8, color='white',
                    weight='bold', zorder=2, wrap=True
                )
            else:
                # Escrever número e guardar para caixa de texto externa
                ax.text(
                    cx, cy, str(contador_pequenos),
                    ha='center', va='center', fontsize=7, color='white',
                    weight='bold', zorder=2
                )
                anotacoes_externas.append(f"{contador_pequenos} = {d_nome} ({val:.0f} GWh)")
                contador_pequenos += 1

# Configurações de eixos e limites
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_axis_off()

# Título curto e informativo
ax.set_title("Consumo de energia por região e distrito em 2025 (GWh)", fontsize=13, pad=12, weight='bold')

# Legenda das regiões fora da área do treemap (à direita) - ordem estritamente correspondente a regioes_ordenadas
patches_legenda = [
    mpatches.Patch(color=cores_regioes[reg], label=reg)
    for reg in regioes_ordenadas if reg in cores_regioes
]

legenda = ax.legend(
    handles=patches_legenda,
    title="Regiões",
    loc="upper left",
    bbox_to_anchor=(1.02, 1.0),
    frameon=False
)

# Adicionar caixa de texto com os distritos pequenos abaixo da legenda
if anotacoes_externas:
    texto_caixa = "Distritos de pequena área:\n" + "\n".join(anotacoes_externas)
    ax.text(
        1.02, 0.65, texto_caixa,
        transform=ax.transAxes,
        fontsize=7,
        verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#cccccc', alpha=0.9)
    )

# Gravar a figura
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
