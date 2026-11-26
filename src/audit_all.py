"""Auditoria global: aplica o nó de integridade a todos os scripts de figuras gerados."""
from agents.integrity_check import bar_axis_findings, count_bar_charts
from common import FIGURES

linhas = ["| Script | Gráficos de barras | Resultado |", "|---|---|---|"]
for path in sorted((FIGURES / "code").glob("*.py")):
    code = path.read_text(encoding="utf-8")
    n = count_bar_charts(code)
    findings = bar_axis_findings(code)
    if n == 0:
        res = "n/a (sem barras)"
    elif not findings:
        res = "CONFORME"
    elif "contraexemplo" in path.stem:
        res = "VIOLA (esperado: contraexemplo intencional)"
    else:
        res = "VIOLA: " + findings[0]
    linhas.append(f"| {path.stem} | {n} | {res} |")

texto = "\n".join(linhas)
print(texto)
(FIGURES / "logs").mkdir(exist_ok=True)
(FIGURES / "logs" / "integrity_audit.md").write_text(texto + "\n", encoding="utf-8")