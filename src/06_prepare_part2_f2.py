"""Etapa 6a: dados para a Parte II, Fase 2."""
import pandas as pd

from common import DATA_CLEAN

# 1) Consumo anual nacional (só anos completos)
nac = pd.read_csv(DATA_CLEAN / "p2_serie_nacional.csv", parse_dates=["data"])
nac["ano"] = nac["data"].dt.year
meses = nac.groupby("ano")["data"].count()
completos = meses[meses == 12].index
anual = (nac[nac["ano"].isin(completos)]
         .groupby("ano", as_index=False)[["bt_gwh", "mt_gwh", "total_gwh"]].sum())
anual["var_pct"] = anual["total_gwh"].pct_change() * 100
anual.to_csv(DATA_CLEAN / "p2_anual_nacional.csv", index=False)
print("Anos completos:", list(completos))
print(anual.round(1).to_string(index=False))

# 2) Concelho x mês, BT vs MT/AT/MAT (todos os meses) para o tratamento de sobreposição
df = pd.read_csv(DATA_CLEAN / "consumos_concelho.csv",
                 dtype={"cod_distrito": str, "cod_concelho": str}, parse_dates=["data"])
reg = pd.read_csv(DATA_CLEAN / "p1_distrito_variacao.csv")[["distrito", "regiao"]]
piv = (df.pivot_table(index=["concelho", "distrito", "data"], columns="nivel_tensao",
                      values="consumo_kwh", aggfunc="sum", fill_value=0)
       .div(1e6).rename(columns={"BT": "bt_gwh", "MT/AT/MAT": "mt_gwh"}).reset_index())
piv.columns.name = None
piv = piv.merge(reg, on="distrito", how="left")
assert piv["regiao"].notna().all()
piv = piv[["concelho", "distrito", "regiao", "data", "bt_gwh", "mt_gwh"]]
piv.to_csv(DATA_CLEAN / "p2_concelho_mes_bt_mt.csv", index=False)

ambos = ((piv["bt_gwh"] > 0) & (piv["mt_gwh"] > 0)).sum()
print(f"\nConcelho x mês: {len(piv):,} linhas (esperado {278 * 69:,}); "
      f"com BT e MT > 0: {ambos:,}; excluídas em log-log: {len(piv) - ambos:,}")