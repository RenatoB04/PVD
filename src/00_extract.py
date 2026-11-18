"""Etapa 1a: download completo do dataset da E-REDES."""
import hashlib
import json
from datetime import datetime, timezone

import pandas as pd
import requests
from common import DATA_RAW

BASE = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets"
DATASET_ID = "3-consumos-faturados-por-municipio-ultimos-10-anos"
OUT_FILE = DATA_RAW / "consumos_municipio.csv"
MANIFEST = DATA_RAW / "manifest.json"


def download() -> tuple[str, int]:
    """Descarrega o CSV completo em streaming. Devolve (sha256, nº de bytes)."""
    url = f"{BASE}/{DATASET_ID}/exports/csv"
    sha, total = hashlib.sha256(), 0
    with requests.get(url, params={"delimiter": ";"}, stream=True,
                      timeout=(30, 600)) as resp:
        resp.raise_for_status()
        with open(OUT_FILE, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                sha.update(chunk)
                total += len(chunk)
    return sha.hexdigest(), total


def main() -> None:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    print("A descarregar o dataset completo (pode demorar alguns minutos)...")
    sha, size = download()

    df = pd.read_csv(OUT_FILE, sep=";", dtype=str)
    manifest = {
        "fonte": "E-REDES Open Data Portal",
        "dataset_id": DATASET_ID,
        "url": f"https://e-redes.opendatasoft.com/explore/dataset/{DATASET_ID}/",
        "licenca": "CC BY 4.0",
        "descarregado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ficheiro": OUT_FILE.name,
        "bytes": size,
        "sha256": sha,
        "linhas": len(df),
        "colunas": list(df.columns),
        "periodo": [df["data"].min(), df["data"].max()],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    print(f"Ficheiro: {OUT_FILE} ({size / 1e6:.1f} MB)")
    print(f"Linhas: {len(df):,}")
    print(f"Período: {manifest['periodo'][0]} a {manifest['periodo'][1]}")
    print(f"Manifesto: {MANIFEST}")


if __name__ == "__main__":
    main()