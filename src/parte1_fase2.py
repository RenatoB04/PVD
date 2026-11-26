"""Parte I, Fase 2: seleção agêntica da geometria + geração das figuras."""
import sys

from agents.chart_selector import run_selected
from parte1_fase1 import DESC_CONC

DESC_REGIAO = """CSV (separador vírgula), 1 linha por região (5), ano 2025. Colunas:
- regiao (str): Norte, Centro, Lisboa e Vale do Tejo, Alentejo, Algarve
- total_gwh (float): consumo anual total em GWh
- n_concelhos (int)
Ler com pd.read_csv(DATA_PATH)."""

DESC_DISTRITO = """CSV (separador vírgula), 1 linha por distrito (18), ano 2025. Colunas:
- regiao (str): região a que o distrito pertence
- distrito (str)
- total_gwh, bt_gwh, mt_gwh (float): consumo anual total, em baixa tensão e em MT/AT/MAT, em GWh
- n_concelhos (int)
Ler com pd.read_csv(DATA_PATH)."""

DESC_CONCELHO_MES = """CSV (separador vírgula), 1 linha por concelho e mês de 2025 (278 x 12). Colunas:
- concelho (str), distrito (str), regiao (str)
- mes (int 1-12), mes_nome (str: Jan, Fev, ..., Dez)
- consumo_gwh (float): consumo do concelho nesse mês, em GWh
Ler com pd.read_csv(DATA_PATH)."""

PEDIDOS = [
    {"name": "p1f2_regiao", "data": "data/clean/f2_regiao.csv", "desc": DESC_REGIAO,
     "question": "Qual o consumo total de eletricidade em 2025 de cada região?"},
    {"name": "p1f2_distritos", "data": "data/clean/f2_distrito.csv", "desc": DESC_DISTRITO,
     "question": "Como se compara o consumo total de 2025 entre os 18 distritos?"},
    {"name": "p1f2_concelhos", "data": "data/clean/p1_concelho_2025.csv", "desc": DESC_CONC,
     "question": "Que concelhos consomem mais eletricidade em 2025 (total_gwh)?"},
    {"name": "p1f2_concelho_mes", "data": "data/clean/f2_concelho_mes.csv",
     "desc": DESC_CONCELHO_MES,
     "question": "Como varia ao longo dos meses de 2025 o consumo dos concelhos?"},
    {"name": "p1f2_hist_total", "data": "data/clean/p1_concelho_2025.csv", "desc": DESC_CONC,
     "question": "Qual é a forma da distribuição do consumo anual total (total_gwh) dos 278 "
                 "concelhos (assimetria, caudas, moda), sem comparar concelhos individuais?"},
    {"name": "p1f2_dist_regiao", "data": "data/clean/p1_concelho_2025.csv", "desc": DESC_CONC,
     "question": "Compara a mediana e a dispersão da quota de baixa tensão (quota_bt_pct) "
                 "dos concelhos entre as 5 regiões."},
    {"name": "p1f2_forma_regiao", "data": "data/clean/p1_concelho_2025.csv", "desc": DESC_CONC,
     "question": "Compara a forma completa da distribuição (densidade, assimetria, "
                 "multimodalidade) da quota de baixa tensão (quota_bt_pct) dos concelhos "
                 "entre as 5 regiões."},
    {"name": "p1f2_dist_distrito", "data": "data/clean/p1_concelho_2025.csv", "desc": DESC_CONC,
     "question": "Compara a mediana e a dispersão da quota de baixa tensão (quota_bt_pct) "
                 "dos concelhos entre os 18 distritos."},
    {"name": "p1f2_treemap", "data": "data/clean/f2_distrito.csv", "desc": DESC_DISTRITO,
     "question": "Como se reparte o consumo total de 2025 por região e, dentro de cada "
                 "região, por distrito?"},
]

if __name__ == "__main__":
    nomes = sys.argv[1:]          # opcional: correr só algumas figuras
    resumo = []
    for p in PEDIDOS:
        if nomes and p["name"] not in nomes:
            continue
        print(f"\n{'=' * 70}\n{p['name']}\n{'=' * 70}")
        try:
            choice, final = run_selected(p["name"], p["data"], p["desc"], p["question"])
            resumo.append((p["name"], choice["geometry"], final["status"], final["iteration"]))
        except Exception as exc:
            print(f"[{p['name']}] ERRO: {exc}")
            resumo.append((p["name"], "-", "erro", 0))

    print("\n=== Resumo ===")
    for nome, geom, estado, it in resumo:
        print(f"  {nome:22s} {geom:18s} {estado:11s} {it} iteração(ões)")