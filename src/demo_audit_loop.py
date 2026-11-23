"""Demonstração: o auditor de cores rejeita uma paleta má e o gerador reescreve."""
from agents.audit_color import make_color_auditor
from agents.graph import run_chart
from parte1_fase1 import DESC_DM

SPEC = ("Heatmap do consumo mensal (consumo_gwh) por distrito (linhas) e mês (colunas, Jan a Dez). "
        "Usa obrigatoriamente a paleta 'jet' (colormap) para a cor das células. "
        "Barra de cor rotulada 'Consumo (GWh)'. Título e eixos em português.")

run_chart("demo_auditor_jet", SPEC, data_path="data/clean/p1_distrito_mes_2025.csv",
          data_description=DESC_DM,
          validators=[make_color_auditor(SPEC, "demo_auditor_jet")], use_critic=False)