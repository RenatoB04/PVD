"""Demonstração: as regras rejeitam barras com 278 categorias e o LLM corrige."""
from agents.chart_selector import build_selector_graph, select_chart
from common import FIGURES

q = ("Compara o consumo total (total_gwh) de 2025 dos 278 concelhos. "
     "O cliente exige um gráfico de barras com TODOS os concelhos (top_n = 0).")
sel = select_chart(q, "data/clean/p1_concelho_2025.csv")

print("\n--- Histórico ---")
for h in sel["history"]:
    print(h)
print("\nEscolha final:", sel["choice"])
print("Erros finais:", sel["errors"])

FIGURES.mkdir(exist_ok=True)
(FIGURES / "selector_diagram.mmd").write_text(
    build_selector_graph().get_graph().draw_mermaid(), encoding="utf-8")
print("\nDiagrama guardado em figures/selector_diagram.mmd")