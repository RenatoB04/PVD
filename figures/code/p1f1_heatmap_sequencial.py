# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/p1_distrito_mes_2025.csv'
OUTPUT_PATH = 'figures/p1f1_heatmap_sequencial.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ler os dados
df = pd.read_csv(DATA_PATH)

# Calcular o consumo anual total por distrito para ordenação
ordem_distritos = df.groupby('distrito')['consumo_gwh'].sum().sort_values(ascending=False).index

# Criar a tabela pivot para o heatmap
heatmap_data = df.pivot(index='distrito', columns='mes', values='consumo_gwh')

# Reordenar as linhas pelo consumo total decrescente
heatmap_data = heatmap_data.reindex(ordem_distritos)

# Configurar a figura
plt.figure(figsize=(10, 6))
sns.set_style("white")

# Gerar o heatmap
ax = sns.heatmap(
    heatmap_data,
    cmap='viridis',
    cbar_kws={'label': 'Consumo (GWh)'},
    xticklabels=['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
)

# Rótulos e título
plt.title('Consumo mensal de eletricidade por distrito (2025)', fontsize=14, pad=20)
plt.xlabel('Mês', fontsize=12)
plt.ylabel('Distrito', fontsize=12)

# Ajustes finais
plt.tight_layout()

# Gravar e fechar
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
