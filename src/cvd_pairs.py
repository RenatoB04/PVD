"""Pares de regiões mais próximos sob visão normal e daltonismo (Okabe-Ito)."""
import itertools

import numpy as np
from matplotlib.colors import to_rgb

from common import FIGURES
from cvd_report import KINDS, jab, simulate

REG = {"Norte": "#0072B2", "Centro": "#E69F00", "Lisboa e Vale do Tejo": "#D55E00",
       "Alentejo": "#009E73", "Algarve": "#CC79A7"}
nomes = list(REG)
cores = np.array([to_rgb(h) for h in REG.values()])

linhas = ["| Condição | 1.º par mais próximo | ΔE | 2.º par | ΔE | 3.º par | ΔE |",
          "|---|---|---|---|---|---|---|"]
for kind, label in KINDS.items():
    c = jab(simulate(cores, kind))
    pares = sorted((float(np.linalg.norm(c[i] - c[j])), nomes[i], nomes[j])
                   for i, j in itertools.combinations(range(len(nomes)), 2))
    cel = " | ".join(f"{a} / {b} | {d:.1f}" for d, a, b in pares[:3])
    linhas.append(f"| {label} | {cel} |")

texto = "\n".join(linhas)
print(texto)
(FIGURES / "cvd").mkdir(parents=True, exist_ok=True)
(FIGURES / "cvd" / "pares_regioes.md").write_text(texto + "\n", encoding="utf-8")