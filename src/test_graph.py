"""Teste do grafo: um caso simples e um caso que força o ciclo de correção."""
import re

from agents.graph import build_graph, run_chart
from common import FIGURES


def requires_axis_labels(code: str) -> list[str]:
    """Validador de demonstração: exige rótulos nos dois eixos."""
    issues = []
    if not re.search(r"xlabel", code):
        issues.append("Falta o rótulo do eixo x (xlabel).")
    if not re.search(r"ylabel", code):
        issues.append("Falta o rótulo do eixo y (ylabel).")
    return issues


def requires_grid(code: str) -> list[str]:
    """Validador de demonstração: obriga a uma 2.ª volta do ciclo."""
    return [] if "grid" in code else ["Adiciona linhas de grelha suaves (ax.grid) ao gráfico."]


SPEC = ("Gráfico de barras horizontais com o consumo total de 2025 (em TWh) por distrito, "
        "ordenado do maior para o menor. Somar os dois níveis de tensão. "
        "Eixo do consumo a começar em zero.")

if __name__ == "__main__":
    print("=== Teste 1: caso simples ===")
    run_chart("demo_distritos", SPEC, validators=[requires_axis_labels])

    print("\n=== Teste 2: força o ciclo de correção ===")
    run_chart("demo_ciclo", SPEC, validators=[requires_axis_labels, requires_grid])

    # Diagrama do grafo para o relatório (colar em https://mermaid.live)
    FIGURES.mkdir(exist_ok=True)
    mermaid = build_graph([], True).get_graph().draw_mermaid()
    (FIGURES / "graph_diagram.mmd").write_text(mermaid, encoding="utf-8")
    print("\nDiagrama Mermaid guardado em figures/graph_diagram.mmd")