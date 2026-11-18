"""Verificações de sanidade ao dataset limpo (agregado por concelho)."""
import pandas as pd
from common import DATA_CLEAN

df = pd.read_csv(DATA_CLEAN / "consumos_concelho.csv",
                 dtype={"cod_distrito": str, "cod_concelho": str},
                 parse_dates=["data"])

print(df.dtypes, "\n")
print("Concelhos (nomes):", df["concelho"].nunique(),
      "| Concelhos (códigos):", df["cod_concelho"].nunique())
print("Valores nulos no consumo:", df["consumo_kwh"].isna().sum())
print("Valores negativos:", (df["consumo_kwh"] < 0).sum())

# Cobertura: concelhos x meses x 2 níveis de tensão
meses = df["data"].nunique()
esperado = df["concelho"].nunique() * meses * 2
print(f"\nMeses: {meses} | Linhas: {len(df):,} | Esperado: {esperado:,} "
      f"| Em falta: {esperado - len(df):,}")

cobertura = df.groupby("concelho")["data"].nunique()
print("\nConcelhos com menos meses do que o total:")
print(cobertura[cobertura < meses].sort_values().to_string() or "nenhum")

# Total mensal em GWh (deteta último mês incompleto)
total = (df.groupby("data")["consumo_kwh"].sum() / 1e6).round(1)
print("\nConsumo total por mês (GWh), primeiros e últimos:")
print(total.head(4).to_string())
print("...")
print(total.tail(8).to_string())