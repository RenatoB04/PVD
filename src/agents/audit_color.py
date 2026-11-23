"""Nó de auditoria de cores (Parte I, Fase 1).

Valida se as paletas do código gerado são adequadas à natureza dos dados
(contínuos vs. categóricos), segundo Wilke, cap. 4. Usado como validador no grafo.
"""
import json
import re
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from common import FIGURES, get_llm

# --------------------------------------------------------------------------
# Catálogo de paletas (nomes em minúsculas, sem o sufixo _r)
# --------------------------------------------------------------------------
CATALOG = {
    "sequential": {"viridis", "plasma", "inferno", "magma", "cividis", "blues",
                   "greens", "reds", "oranges", "purples", "greys", "ylorrd",
                   "ylorbr", "ylgn", "ylgnbu", "gnbu", "bugn", "bupu", "orrd",
                   "pubu", "pubugn", "purd", "rdpu", "rocket", "mako", "flare",
                   "crest"},
    "diverging": {"rdbu", "rdylbu", "rdylgn", "rdgy", "brbg", "piyg", "prgn",
                  "puor", "spectral", "coolwarm", "bwr", "seismic", "vlag",
                  "icefire"},
    "qualitative": {"set1", "set2", "set3", "tab10", "tab20", "tab20b", "tab20c",
                    "dark2", "paired", "pastel1", "pastel2", "accent",
                    "colorblind", "deep", "muted", "bright"},
    "banned": {"jet", "rainbow", "hsv", "gist_rainbow", "nipy_spectral",
               "gist_ncar", "prism", "flag"},
}
CENTER_RE = re.compile(r"TwoSlopeNorm|CenteredNorm|vcenter|center\s*=|vmin\s*=\s*-",
                       re.IGNORECASE)


def detect_palettes(code: str) -> tuple[dict[str, str], set[str]]:
    """Procura nomes de paletas conhecidas em literais de texto e cores hexadecimais."""
    literals = set(re.findall(r"""['"]([A-Za-z0-9_]+)['"]""", code))
    found = {}
    for lit in literals:
        key = lit.lower()
        key = key[:-2] if key.endswith("_r") else key
        for kind, names in CATALOG.items():
            if key in names:
                found[lit] = kind
    hexes = set(re.findall(r"#[0-9A-Fa-f]{6}\b", code))
    return found, hexes


# --------------------------------------------------------------------------
# Juiz LLM
# --------------------------------------------------------------------------
class ColorMapping(BaseModel):
    variable: str = Field(description="Variável de dados mapeada em cor.")
    nature: Literal["categorica_nominal", "categorica_ordinal",
                    "continua_sequencial", "continua_divergente"]
    palette: str = Field(description="Paleta ou lista de cores usada.")
    adequate: bool
    problem: str = Field(description="Problema e correção sugerida; vazio se adequada.")


class ColorAudit(BaseModel):
    mappings: list[ColorMapping]


AUDIT_SYSTEM = """És um auditor de cor em visualização de dados (Wilke, cap. 4 \
'Color scales' e cap. 19). Recebes a especificação da figura, o código Python \
gerado e as paletas detetadas por análise estática. Identifica TODAS as variáveis \
de dados mapeadas em cor (hue, cmap, palette, cores de barras por valor, etc.) e \
classifica cada uma:
- categorica_nominal: categorias sem ordem -> paleta QUALITATIVA (matizes distintos, \
no máximo ~8 categorias)
- categorica_ordinal ou continua_sequencial: valores ordenados -> paleta SEQUENCIAL \
(luminosidade monótona)
- continua_divergente: valores com ponto médio significativo (ex.: variação em torno \
de 0) -> paleta DIVERGENTE centrada nesse ponto
Regras: paletas arco-íris são sempre inadequadas; uma paleta qualitativa para dados \
contínuos, ou sequencial para categorias nominais, é inadequada. Uma cor única para \
toda a série não é um mapeamento (ignora). Para listas de cores hexadecimais, avalia \
pela natureza (ex.: 5 cores de matizes distintos = qualitativa). Se adequate=false, \
explica o problema em português europeu, de forma acionável. Se a figura não mapeia \
dados em cor, devolve mappings vazio."""


# --------------------------------------------------------------------------
# Fábrica do validador
# --------------------------------------------------------------------------
def make_color_auditor(spec: str, log_name: str | None = None):
    """Devolve um validador `codigo -> lista de problemas` para o grafo."""
    records: list[dict] = []

    def audit_color(code: str) -> list[str]:
        found, hexes = detect_palettes(code)
        record = {"paletas_detetadas": found, "n_hex": len(hexes), "mappings": [],
                  "issues": []}
        issues: list[str] = []

        # Camada 1: regras determinísticas
        for name, kind in found.items():
            if kind == "banned":
                issues.append(
                    f"A paleta '{name}' (arco-íris) é proibida: não é perceptualmente "
                    "uniforme nem segura para daltónicos. Usa uma paleta sequencial "
                    "(viridis, cividis), divergente centrada ou qualitativa (Okabe-Ito).")
        if any(k == "diverging" for k in found.values()) and not CENTER_RE.search(code):
            issues.append(
                "Foi usada uma paleta divergente sem centrar no ponto médio. "
                "Usa matplotlib.colors.TwoSlopeNorm(vcenter=0) (ou center=0 no seaborn).")

        # Camada 2: juiz LLM (só se a camada 1 estiver limpa)
        if not issues:
            human = (f"Especificação da figura:\n{spec}\n\n"
                     f"Paletas detetadas (análise estática): {found or 'nenhuma'}; "
                     f"cores hexadecimais distintas: {len(hexes)}\n\n"
                     f"Código:\n```python\n{code}\n```")
            try:
                audit = get_llm(0.0).with_structured_output(ColorAudit).invoke(
                    [SystemMessage(AUDIT_SYSTEM), HumanMessage(human)])
                for m in (audit.mappings if audit else []):
                    record["mappings"].append(m.model_dump())
                    print(f"    [cor] {m.variable} ({m.nature}) -> {m.palette}: "
                          f"{'OK' if m.adequate else 'INADEQUADA'}")
                    if not m.adequate:
                        issues.append(f"Cor: a variável '{m.variable}' ({m.nature}) usa "
                                      f"'{m.palette}': {m.problem}")
            except Exception as exc:  # o auditor não deve bloquear o grafo
                print(f"    (aviso) auditor LLM indisponível: {exc}")

        record["issues"] = issues
        records.append(record)
        if log_name:
            log_dir = FIGURES / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            (log_dir / f"audit_{log_name}.json").write_text(
                json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        return issues

    audit_color.__name__ = "audit_color"
    return audit_color