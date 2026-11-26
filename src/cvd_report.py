"""Parte II, Fase 2: conformidade das paletas e simulação de daltonismo (Wilke, cap. 19).

Uso:
    python src/cvd_report.py                                  # todas as figuras p*.png
    python src/cvd_report.py p1f1_scatter_escalas p2f2_sobreposicao
"""
import itertools
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from colorspacious import cspace_convert
from matplotlib import colormaps
from matplotlib.colors import to_rgb
from PIL import Image
from scipy.stats import spearmanr

from agents.audit_color import detect_palettes
from common import FIGURES

OUT = FIGURES / "cvd"
KINDS = {"normal": "Visão normal",
         "deuteranopia": "Deuteranopia (sem cones verdes)",
         "protanopia": "Protanopia (sem cones vermelhos)"}
CVD = {"deuteranopia": {"name": "sRGB1+CVD", "cvd_type": "deuteranomaly", "severity": 100},
       "protanopia": {"name": "sRGB1+CVD", "cvd_type": "protanomaly", "severity": 100}}
MIN_DE = 10.0    # heurística: distância mínima entre cores (CAM02-UCS)
MIN_RHO = 0.98   # heurística: monotonia da luminosidade numa paleta sequencial


def simulate(rgb, kind: str) -> np.ndarray:
    rgb = np.asarray(rgb, dtype=float)
    out = rgb if kind == "normal" else cspace_convert(rgb, CVD[kind], "sRGB1")
    return np.clip(out, 0, 1)


def jab(rgb) -> np.ndarray:
    return cspace_convert(rgb, "sRGB1", "CAM02-UCS")


# ---- testes por tipo de paleta -------------------------------------------------
def test_qualitative(colors: np.ndarray, labels: list[str]) -> dict:
    out = {}
    for kind in KINDS:
        c = jab(simulate(colors, kind))
        d, i, j = min((float(np.linalg.norm(c[a] - c[b])), a, b)
                      for a, b in itertools.combinations(range(len(c)), 2))
        out[kind] = {"valor": round(d, 1), "ok": d >= MIN_DE, "par_critico": [labels[i], labels[j]]}
    return out


def test_sequential(cmap) -> dict:
    rgb = cmap(np.linspace(0, 1, 256))[:, :3]
    out = {}
    for kind in KINDS:
        rho = abs(float(spearmanr(jab(simulate(rgb, kind))[:, 0], np.arange(256))[0]))
        out[kind] = {"valor": round(rho, 3), "ok": rho >= MIN_RHO}
    return out


def test_diverging(cmap) -> dict:
    ends = np.array([cmap(0.1)[:3], cmap(0.9)[:3]])
    out = {}
    for kind in KINDS:
        c = jab(simulate(ends, kind))
        d = float(np.linalg.norm(c[0] - c[1]))
        out[kind] = {"valor": round(d, 1), "ok": d >= MIN_DE}
    return out


def resolve_cmap(name: str):
    for candidate in (name, name.lower()):
        try:
            return colormaps[candidate]
        except KeyError:
            pass
    return None


def is_grey(h: str) -> bool:
    r, g, b = to_rgb(h)
    return max(r, g, b) - min(r, g, b) < 0.08


# ---- recolha e avaliação das paletas dos scripts gerados -----------------------
def collect_palettes() -> dict:
    pal: dict = {}
    for path in sorted((FIGURES / "code").glob("p*.py")):
        named, hexes = detect_palettes(path.read_text(encoding="utf-8"))
        for lit, kind in named.items():
            if kind != "banned":
                e = pal.setdefault(f"{lit} ({kind})", {"tipo": kind, "nome": lit, "figuras": []})
                e["figuras"].append(path.stem)
        chroma = sorted({h.upper() for h in hexes if not is_grey(h)})
        if len(chroma) >= 2:
            e = pal.setdefault("hex: " + " ".join(chroma),
                               {"tipo": "qualitative", "cores": chroma, "figuras": []})
            e["figuras"].append(path.stem)
    return pal


def evaluate(e: dict):
    """(tipo legível, critério, resultados) ou None se a paleta não for resolvível."""
    if "cores" in e:
        colors = np.array([to_rgb(h) for h in e["cores"]])
        return "qualitativa (hex)", "ΔE mínimo entre cores", test_qualitative(colors, e["cores"])
    if e["tipo"] == "qualitative":
        try:
            colors = np.array(sns.color_palette(e["nome"]))[:12]
        except Exception:
            return None
        return ("qualitativa", "ΔE mínimo entre cores",
                test_qualitative(colors, [f"cor {i + 1}" for i in range(len(colors))]))
    cmap = resolve_cmap(e["nome"])
    if cmap is None:
        return None
    if e["tipo"] == "sequential":
        return "sequencial", "|ρ| luminosidade vs posição", test_sequential(cmap)
    return "divergente", "ΔE entre extremos", test_diverging(cmap)


def palette_report() -> None:
    rows, data = [], []
    for key, e in collect_palettes().items():
        res = evaluate(e)
        if res is None:
            print(f"(aviso) paleta não resolvida: {key}")
            continue
        tipo, criterio, r = res
        estado = "CONFORME" if all(v["ok"] for v in r.values()) else "ATENÇÃO"
        cells = " | ".join(f"{r[k]['valor']} {'OK' if r[k]['ok'] else 'FALHA'}" for k in KINDS)
        rows.append(f"| {key} | {tipo} | {criterio} | {cells} | {len(set(e['figuras']))} | {estado} |")
        data.append({"paleta": key, "tipo": tipo, "criterio": criterio, "resultados": r,
                     "figuras": sorted(set(e["figuras"])), "estado": estado})
    header = ("| Paleta | Tipo | Critério | Visão normal | Deuteranopia | Protanopia | Nº figuras | Estado |\n"
              "|---|---|---|---|---|---|---|---|\n")
    note = (f"\nLimiares heurísticos: ΔE ≥ {MIN_DE} (CAM02-UCS) e |ρ| ≥ {MIN_RHO}. "
            "Simulação: Machado et al. (2009) via colorspacious, severidade 100 (dicromacia).\n")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "palette_conformity.md").write_text(header + "\n".join(rows) + "\n" + note, encoding="utf-8")
    (OUT / "palette_conformity.json").write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                                 encoding="utf-8")
    print("\n" + header + "\n".join(rows) + note)


# ---- simulação nas figuras ------------------------------------------------------
def simulate_figure(png) -> None:
    img = np.asarray(Image.open(png).convert("RGB"), dtype=float) / 255.0
    h, w = img.shape[:2]
    fig, axes = plt.subplots(1, 3, figsize=(18, 18 * h / (3 * w) + 0.8))
    for ax, kind in zip(axes, KINDS):
        ax.imshow(simulate(img, kind))
        ax.set_title(KINDS[kind], fontsize=12)
        ax.axis("off")
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{png.stem}_cvd.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    names = sys.argv[1:]
    pngs = ([FIGURES / f"{n}.png" for n in names] if names else sorted(FIGURES.glob("p*.png")))
    for p in pngs:
        print(f"[daltonismo] {p.name}")
        simulate_figure(p)
    palette_report()
    print(f"\nFiguras simuladas e relatório em {OUT}")