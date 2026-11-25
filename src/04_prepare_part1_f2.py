"""Etapa 4a: datasets derivados para a Parte I, Fase 2 (ano 2025)."""
import pandas as pd

from common import DATA_CLEAN

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

conc = pd.read_csv(DATA_CLEAN / "p1_concelho_2025.csv")
# colunas: concelho, distrito, regiao, bt_gwh, mt_gwh, total_gwh, quota_bt_pct, perfil

# 1) Por região (5 categorias)
reg = (conc.groupby("regiao", as_index=False)
       .agg(total_gwh=("total_gwh", "sum"), n_concelhos=("concelho", "count")))
reg.to_csv(DATA_CLEAN / "f2_regiao.csv", index=False)

# 2) Por distrito (18 categorias, com a região a que pertencem)
dist = (conc.groupby(["regiao", "distrito"], as_index=False)
        .agg(total_gwh=("total_gwh", "sum"), bt_gwh=("bt_gwh", "sum"),
             mt_gwh=("mt_gwh", "sum"), n_concelhos=("concelho", "count")))
dist.to_csv(DATA_CLEAN / "f2_distrito.csv", index=False)

# 3) Concelho x mês (278 x 12)
df = pd.read_csv(DATA_CLEAN / "consumos_concelho.csv",
                 dtype={"cod_distrito": str, "cod_concelho": str},
                 parse_dates=["data"])
d = df[df["data"].dt.year == 2025].copy()
d["mes"] = d["data"].dt.month
cm = (d.groupby(["concelho", "mes"], as_index=False)["consumo_kwh"].sum())
cm["consumo_gwh"] = cm["consumo_kwh"] / 1e6
cm["mes_nome"] = cm["mes"].map(lambda m: MESES[m - 1])
cm = cm.merge(conc[["concelho", "distrito", "regiao"]], on="concelho", how="left")
assert cm["regiao"].notna().all(), "Concelhos sem região"
cm = cm[["concelho", "distrito", "regiao", "mes", "mes_nome", "consumo_gwh"]]
cm.to_csv(DATA_CLEAN / "f2_concelho_mes.csv", index=False)

# Verificações
print("Regiões:\n", reg.round(1).to_string(index=False))
print(f"\nDistritos: {len(dist)} | concelhos por distrito: "
      f"min={dist['n_concelhos'].min()}, max={dist['n_concelhos'].max()}")
print(f"Concelho x mês: {len(cm):,} linhas (esperado {278 * 12:,})")
print(f"Soma total (GWh): conc={conc['total_gwh'].sum():.1f} | "
      f"distritos={dist['total_gwh'].sum():.1f} | concelho-mês={cm['consumo_gwh'].sum():.1f}")
print("\nObservações (concelhos) por região:",
      conc["regiao"].value_counts().to_dict())
print("Observações (concelhos) por distrito, mínimo:",
      conc["distrito"].value_counts().min())