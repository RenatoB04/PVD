"""Testa o auditor de cores com 4 trechos de código conhecidos."""
from agents.audit_color import make_color_auditor

SPEC_CAT = ("Scatter de bt_gwh vs mt_gwh por concelho, com cor = regiao "
            "(categórica nominal: Norte, Centro, Lisboa e Vale do Tejo, Alentejo, Algarve).")
SPEC_VAR = "Barras horizontais da variação percentual (var_pct, positiva ou negativa) por distrito, coloridas pelo valor."

CASOS = {
    "1) jet num gráfico categórico (esperado: REPROVA, regra determinística)": (
        SPEC_CAT,
        'import seaborn as sns, pandas as pd\ndf = pd.read_csv(DATA_PATH)\n'
        'sns.scatterplot(data=df, x="bt_gwh", y="mt_gwh", hue="regiao", palette="jet")\n'),
    "2) viridis em categorias nominais (esperado: REPROVA, juiz LLM)": (
        SPEC_CAT,
        'import seaborn as sns, pandas as pd\ndf = pd.read_csv(DATA_PATH)\n'
        'sns.scatterplot(data=df, x="bt_gwh", y="mt_gwh", hue="regiao", palette="viridis")\n'),
    "3) RdBu sem centrar em 0 (esperado: REPROVA, regra determinística)": (
        SPEC_VAR,
        'import matplotlib.pyplot as plt, pandas as pd\ndf = pd.read_csv(DATA_PATH)\n'
        'cmap = plt.get_cmap("RdBu")\nplt.barh(df["distrito"], df["var_pct"], color=cmap(df["var_pct"]))\n'),
    "4) Okabe-Ito em categorias nominais (esperado: APROVA)": (
        SPEC_CAT,
        'import seaborn as sns, pandas as pd\ndf = pd.read_csv(DATA_PATH)\n'
        'cores = ["#0072B2", "#E69F00", "#D55E00", "#009E73", "#CC79A7"]\n'
        'sns.scatterplot(data=df, x="bt_gwh", y="mt_gwh", hue="regiao", palette=cores)\n'),
}

for titulo, (spec, codigo) in CASOS.items():
    print(f"\n=== {titulo}")
    problemas = make_color_auditor(spec)(codigo)
    print("  ->", "APROVADO" if not problemas else "REPROVADO")
    for p in problemas:
        print("     *", p)