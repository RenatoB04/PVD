"""Etapa 3a: datasets derivados para a Parte I."""
import unicodedata

import numpy as np
import pandas as pd
from scipy.stats import skew

from common import DATA_CLEAN


def norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


# Agrupamento simplificado em 5 regiões (documentar no relatório)
REGIAO = {norm(k): v for k, v in {
    "Viana do Castelo": "Norte", "Braga": "Norte", "Porto": "Norte",
    "Vila Real": "Norte", "Bragança": "Norte",
    "Aveiro": "Centro", "Coimbra": "Centro", "Viseu": "Centro",
    "Guarda": "Centro", "Castelo Branco": "Centro", "Leiria": "Centro",
    "Lisboa": "Lisboa e Vale do Tejo", "Santarém": "Lisboa e Vale do Tejo",
    "Setúbal": "Lisboa e Vale do Tejo",
    "Portalegre": "Alentejo", "Évora": "Alentejo", "Beja": "Alentejo",
    "Faro": "Algarve",
}.items()}

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
ANO_BASE, ANO_REF = 2022, 2025  # anos completos (2020 só tem nov-dez)

df = pd.read_csv(DATA_CLEAN / "consumos_concelho.csv",
                 dtype={"cod_distrito": str, "cod_concelho": str},
                 parse_dates=["data"])
df["ano"] = df["data"].dt.year

unknown = {d for d in df["distrito"].unique() if norm(d) not in REGIAO}
assert not unknown, f"Distritos sem região: {unknown}"


def regiao(distrito: str) -> str:
    return REGIAO[norm(distrito)]


# ---- 1) Concelho, ano de referência: BT vs MT/AT/MAT -------------------------
d = df[df["ano"] == ANO_REF]
piv = (d.pivot_table(index=["distrito", "concelho"], columns="nivel_tensao",
                     values="consumo_kwh", aggfunc="sum", fill_value=0)
       .reset_index())
piv.columns.name = None
piv["regiao"] = piv["distrito"].map(regiao)
piv["bt_gwh"] = piv["BT"] / 1e6
piv["mt_gwh"] = piv["MT/AT/MAT"] / 1e6
piv["total_gwh"] = piv["bt_gwh"] + piv["mt_gwh"]
piv["quota_bt_pct"] = 100 * piv["bt_gwh"] / piv["total_gwh"]
piv["perfil"] = np.where(piv["bt_gwh"] > piv["mt_gwh"],
                         "Predomínio BT", "Predomínio MT/AT/MAT")
conc = (piv[["concelho", "distrito", "regiao", "bt_gwh", "mt_gwh",
             "total_gwh", "quota_bt_pct", "perfil"]]
        .sort_values("total_gwh", ascending=False))
conc.to_csv(DATA_CLEAN / "p1_concelho_2025.csv", index=False)

# ---- 2) Distrito x mês (ano de referência) ----------------------------------
dm = (d.groupby(["distrito", d["data"].dt.month.rename("mes")])["consumo_kwh"]
      .sum().div(1e6).rename("consumo_gwh").reset_index())
dm["mes_nome"] = dm["mes"].map(lambda m: MESES[m - 1])
dm.to_csv(DATA_CLEAN / "p1_distrito_mes_2025.csv", index=False)

# ---- 3) Variação % por distrito (ANO_BASE -> ANO_REF) -------------------------
anual = (df[df["ano"].isin([ANO_BASE, ANO_REF])]
         .groupby(["distrito", "ano"])["consumo_kwh"].sum().div(1e6).unstack("ano"))
anual.columns = [f"consumo_{c}_gwh" for c in anual.columns]
anual["var_pct"] = (anual[f"consumo_{ANO_REF}_gwh"]
                    / anual[f"consumo_{ANO_BASE}_gwh"] - 1) * 100
var = anual.reset_index()
var["regiao"] = var["distrito"].map(regiao)
var.to_csv(DATA_CLEAN / "p1_distrito_variacao.csv", index=False)

# ---- Resumo e justificação da escala logarítmica ------------------------------
print(f"Concelhos: {len(conc)} | com mt_gwh = 0: {(conc['mt_gwh'] == 0).sum()}")
print("\nConcelhos por região:")
print(conc["regiao"].value_counts().to_string())
print("\nTop 5 concelhos (total GWh):")
print(conc.head(5)[["concelho", "total_gwh"]].round(1).to_string(index=False))

for col in ["bt_gwh", "mt_gwh"]:
    s = conc.loc[conc[col] > 0, col]
    print(f"\n{col}: min={s.min():.4f}  mediana={s.median():.2f}  max={s.max():.1f}  "
          f"max/min={s.max() / s.min():,.0f}  "
          f"assimetria bruta={skew(s):.2f}  assimetria log10={skew(np.log10(s)):.2f}")

print(f"\nVariação % {ANO_BASE}->{ANO_REF} por distrito:")
print(var.sort_values("var_pct")[["distrito", "var_pct"]].round(1).to_string(index=False))
print("\nFicheiros: p1_concelho_2025.csv, p1_distrito_mes_2025.csv, p1_distrito_variacao.csv")