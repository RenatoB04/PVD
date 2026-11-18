"""Exploração inicial do dataset da E-REDES (amostra + metadados)."""
import json

import pandas as pd
import requests
from common import DATA_RAW

BASE = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets"
DATASET_ID = "3-consumos-faturados-por-municipio-ultimos-10-anos"

DATA_RAW.mkdir(parents=True, exist_ok=True)

# 1) Metadados: título, nº de registos, campos
meta = requests.get(f"{BASE}/{DATASET_ID}", timeout=30)
meta.raise_for_status()
meta = meta.json()
(DATA_RAW / "metadata.json").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
)

print("Título:", meta.get("metas", {}).get("default", {}).get("title"))
print("Nº de registos:", meta.get("records_count"))
print("\nCampos:")
for f in meta.get("fields", []):
    print(f"  - {f['name']:35s} {f['type']:10s} {f.get('label', '')}")

# 2) Amostra de 5000 linhas em CSV
resp = requests.get(
    f"{BASE}/{DATASET_ID}/exports/csv",
    params={"limit": 5000, "delimiter": ";"},
    timeout=120,
)
resp.raise_for_status()
sample_path = DATA_RAW / "sample.csv"
sample_path.write_bytes(resp.content)

df = pd.read_csv(sample_path, sep=";")
print("\nShape da amostra:", df.shape)
print("\nPrimeiras linhas:")
print(df.head(10).to_string())
print("\nTipos e nulos:")
print(pd.DataFrame({"dtype": df.dtypes, "nulos": df.isna().sum(),
                    "distintos": df.nunique()}).to_string())
print("\nEstatísticas numéricas:")
print(df.describe().T.to_string())