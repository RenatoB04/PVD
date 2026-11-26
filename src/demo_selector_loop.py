"""Demonstração: as regras rejeitam uma proposta inválida (injetada) e o LLM corrige."""
from agents.chart_selector import build_selector_graph, select_chart
from common import FIGURES

SEED = {"analysis_type": "comparar_categorias", "geometry": "bar",
        "category_column": "concelho", "second_category_column": "",
        "value_column": "total_gwh", "top_n": 0, "log_scale": False,
        "rationale": "Proposta injetada: barras com todos os concelhos."}

sel = select_chart("Compara o consumo total (total_gwh) de 2025 dos 278 concelhos.",
                   "data/clean/p1_concelho_2025.csv", seed=SEED)

print("\n--- Histórico ---")
for h in sel["history"]:
    print(h)
print("\nEscolha final:", sel["choice"])
print("Erros finais:", sel["errors"])

FIGURES.mkdir(exist_ok=True)
(FIGURES / "selector_diagram.mmd").write_text(
    build_selector_graph().get_graph().draw_mermaid(), encoding="utf-8")