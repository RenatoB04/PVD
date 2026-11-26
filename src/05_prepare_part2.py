"""Etapa 5a: séries temporais para a Parte II, Fase 1."""
import pandas as pd

from common import DATA_CLEAN

df = pd.read_csv(DATA_CLEAN / "consumos_concelho.csv",
                 dtype={"cod_distrito": str, "cod_concelho": str}, parse_dates=["data"])
dreg = pd.read_csv(DATA_CLEAN / "p1_distrito_variacao.csv")[["distrito", "regiao"]]
df = df.merge(dreg, on="distrito", how="left")
assert df["regiao"].notna().all(), "Distritos sem região"

# 1) Série nacional mensal (GWh): BT, MT/AT/MAT e total
nac = (df.pivot_table(index="data", columns="nivel_tensao", values="consumo_kwh", aggfunc="sum")
       .div(1e6).rename(columns={"BT": "bt_gwh", "MT/AT/MAT": "mt_gwh"}))
nac.columns.name = None
nac["total_gwh"] = nac["bt_gwh"] + nac["mt_gwh"]
nac = nac.reset_index()
esperado = pd.date_range(nac["data"].min(), nac["data"].max(), freq="MS")
assert len(esperado) == len(nac), "Há meses em falta na série nacional"
nac.to_csv(DATA_CLEAN / "p2_serie_nacional.csv", index=False)

# 2) Série mensal por região (formato longo)
reg = df.groupby(["data", "regiao"], as_index=False)["consumo_kwh"].sum()
reg["consumo_gwh"] = reg["consumo_kwh"] / 1e6
reg = reg[["data", "regiao", "consumo_gwh"]]
assert reg.groupby("regiao")["data"].nunique().nunique() == 1, "Regiões com nº de meses diferente"
reg.to_csv(DATA_CLEAN / "p2_serie_regiao.csv", index=False)

print(f"Série nacional: {len(nac)} meses ({nac['data'].min():%Y-%m} a {nac['data'].max():%Y-%m})")
print(nac.round(1).head(3).to_string(index=False))
print("...")
print(nac.round(1).tail(3).to_string(index=False))
print(f"\nSérie por região: {len(reg)} linhas = {reg['regiao'].nunique()} regiões x "
      f"{reg['data'].nunique()} meses")
print("Soma nacional vs soma regional (GWh):",
      round(nac["total_gwh"].sum(), 1), round(reg["consumo_gwh"].sum(), 1))