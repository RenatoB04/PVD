# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p2_anual_nacional.csv'
OUTPUT_PATH = 'figures/p2f2_barras_anual.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Ler os dados
df = pd.read_csv(DATA_PATH)

# Preparar a figura
fig, ax = plt.subplots(figsize=(10, 6.5))

# Definir dados
anos = df['ano'].astype(str)
totais = df['total_gwh']
var_pct = df['var_pct']

# Criar gráfico de barras
bars = ax.bar(anos, totais, color='#0072B2', width=0.6)

# Configurar eixo y
y_max = totais.max() * 1.15
ax.set_ylim(0, y_max)
ax.set_ylabel('Consumo anual (GWh)')
ax.set_xlabel('Ano')

# Título
ax.set_title('Consumo anual de eletricidade em Portugal continental, 2021–2025', loc='left', fontsize=14, pad=15, fontweight='bold')

# Remover grelha vertical e espinhas desnecessárias
ax.grid(axis='x', visible=False)
ax.grid(axis='y', linestyle='--', alpha=0.5)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Adicionar valores acima das barras e variações dentro das barras
for i, bar in enumerate(bars):
    height = bar.get_height()
    
    # Valor acima da barra
    val_str = f"{height:,.0f}".replace(",", " ")
    ax.text(
        bar.get_x() + bar.get_width() / 2.,
        height + (y_max * 0.02),
        val_str,
        ha='center',
        va='bottom',
        fontsize=10,
        fontweight='semibold'
    )
    
    # Variação dentro da barra (junto ao topo) para 2022 a 2025
    if i > 0 and not pd.isna(var_pct.iloc[i]):
        v = var_pct.iloc[i]
        # Formatar com sinal explícito e vírgula decimal
        sinal = "+" if v > 0 else ""
        var_str = f"{sinal}{v:.1f}%".replace(".", ",")
        
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height - (y_max * 0.05),
            var_str,
            ha='center',
            va='top',
            fontsize=10,
            color='white',
            fontweight='bold'
        )

# Nota de rodapé
fig.text(
    0.1, 0.02,
    "Anos completos; 2020 e 2026 excluídos por estarem incompletos. Eixo vertical a partir de zero.",
    fontsize=9,
    color='gray',
    ha='left'
)

# Ajustar layout
plt.tight_layout(rect=[0, 0.05, 1, 1])

# Gravar e fechar
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
