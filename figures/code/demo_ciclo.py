# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
DATA_PATH = 'data/clean/consumos_concelho.csv'
OUTPUT_PATH = 'figures/demo_ciclo.png'
Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ler os dados
df = pd.read_csv(DATA_PATH, dtype={'cod_distrito': str, 'cod_concelho': str}, parse_dates=['data'])

# Filtrar para o ano de 2025
df_2025 = df[df['data'].dt.year == 2025].copy()

# Converter consumo de kWh para TWh (1 TWh = 10^9 kWh)
df_2025['consumo_twh'] = df_2025['consumo_kwh'] / 1e9

# Agrupar por distrito e somar o consumo
distritos_consumo = df_2025.groupby('distrito')['consumo_twh'].sum().sort_values(ascending=True)

# Configuração do gráfico
sns.set_theme(style="whitegrid")
fig, ax = plt.subplots(figsize=(10, 6))

# Criar gráfico de barras horizontais
distritos_consumo.plot(kind='barh', ax=ax, color='steelblue')

# Personalização
ax.set_title('Consumo total de energia elétrica por distrito em 2025', fontsize=14, pad=15)
ax.set_xlabel('Consumo total (TWh)', fontsize=12)
ax.set_ylabel('Distrito', fontsize=12)
ax.set_xlim(left=0)

# Remover moldura desnecessária
sns.despine(left=True, bottom=True)
ax.grid(axis='x', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
plt.close()
