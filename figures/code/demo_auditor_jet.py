# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_distrito_mes_2025.csv'
OUTPUT_PATH = 'figures/demo_auditor_jet.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ler os dados
df = pd.read_csv(DATA_PATH)

# Preparar os dados para o heatmap (pivot table)
# Garantir a ordem cronológica dos meses
meses_ordem = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
df['mes_nome'] = pd.Categorical(df['mes_nome'], categories=meses_ordem, ordered=True)
df_pivot = df.pivot(index='distrito', columns='mes_nome', values='consumo_gwh')

# Configurar a figura seguindo princípios de design limpo
plt.figure(figsize=(10, 6))

# Criar o heatmap com paleta 'viridis' (perceptualmente uniforme)
ax = sns.heatmap(
    df_pivot, 
    cmap='viridis', 
    annot=False, 
    cbar_kws={'label': 'Consumo (GWh)'},
    linewidths=0.5,
    linecolor='white'
)

# Rótulos e títulos em português europeu
plt.title('Consumo mensal de energia por distrito (2025)', fontsize=14, pad=15, loc='left')
plt.xlabel('Mês', fontsize=12)
plt.ylabel('Distrito', fontsize=12)

# Ajustes estéticos para remover ruído visual
sns.despine(left=True, bottom=True)

# Gravar e fechar
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
