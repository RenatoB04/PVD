"""Demonstração: o nó de integridade rejeita barras truncadas e o gerador reescreve."""
from agents.graph import run_chart
from agents.integrity_check import check_bar_axis_integrity
from parte2_fase2 import DESC_ANUAL

SPEC = ("Gráfico de barras verticais (ax.bar) do consumo anual total nacional (total_gwh) por ano. "
        "Para realçar as diferenças entre anos, define obrigatoriamente o limite inferior do eixo y como "
        "0.95 vezes o valor mínimo: ax.set_ylim(total.min() * 0.95, total.max() * 1.02). "
        "Rótulos dos eixos em português e título informativo.")

run_chart("demo_integridade", SPEC, data_path="data/clean/p2_anual_nacional.csv",
          data_description=DESC_ANUAL, validators=[check_bar_axis_integrity], use_critic=False)