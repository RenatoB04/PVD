"""Grafo LangGraph cíclico: gerador -> validador -> executor -> crítico visual.

Os validadores são funções `codigo -> lista de problemas` e podem ser
acrescentados por fase (auditoria de cores, integridade de eixos, etc.).
"""
import base64
import json
import operator
import re
import subprocess
import sys
from typing import Annotated, Callable, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from common import (CONCELHO_CSV, CONCELHO_DESC, FIGURES, ROOT,
                    content_to_text, get_llm)

Validator = Callable[[str], list[str]]


# --------------------------------------------------------------------------
# Estado partilhado entre nós
# --------------------------------------------------------------------------
class State(TypedDict, total=False):
    name: str
    spec: str
    data_path: str
    data_description: str
    output_path: str
    code: str
    issues: list[str]       # feedback para o gerador
    stage: str              # último nó que produziu issues
    iteration: int
    max_iter: int
    status: str             # running | approved | unapproved | failed
    last_critique: list[str] 
    log: Annotated[list[dict], operator.add]


# --------------------------------------------------------------------------
# Prompts
# --------------------------------------------------------------------------
GEN_SYSTEM = """És um especialista em visualização de dados em Python. Escreves \
código para gerar UMA figura estática, seguindo os princípios de Claus Wilke \
(Fundamentals of Data Visualization).

Regras obrigatórias:
- Usa apenas pandas, numpy, matplotlib, seaborn, scipy, statsmodels, squarify \
ou joypy.
- As variáveis DATA_PATH e OUTPUT_PATH já estão definidas; NÃO as redefinas. \
Não chames matplotlib.use().
- Lê os dados com pd.read_csv(DATA_PATH, ...) conforme a descrição do dataset.
- Grava a figura com plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight") e \
fecha-a com plt.close(). Nunca uses plt.show().
- Texto da figura em português europeu: título, rótulos dos eixos com unidades, \
legenda quando necessária.
- Figura limpa: sem elementos decorativos, sem sobreposição de texto, etiquetas \
legíveis; figsize aproximado (10, 6).
- Responde APENAS com um bloco ```python ... ``` com o código completo, sem \
explicações.
- Se receberes problemas a corrigir, resolve-os todos e devolve o código completo."""

CRITIC_SYSTEM = """És um revisor de visualizações de dados. Recebes a especificação, \
o código Python que gerou a figura e a imagem. Regras:
- Reporta apenas problemas que vês claramente na imagem ou que confirmas no código.
- NÃO verifiques códigos hexadecimais de cores nem limites numéricos exatos a partir \
dos píxeis: confirma-os no código.
- Em gráficos de barras horizontais (barh) a primeira categoria fica em baixo, salvo \
se o eixo y for invertido: lê o código antes de apontar um erro de ordenação.
- Se receberes problemas da revisão anterior, verifica se foram resolvidos. Não \
repitas críticas já resolvidas e não inventes críticas novas sem evidência clara.
- Marca severe=true apenas para: requisito explícito da especificação não cumprido, \
texto sobreposto ou cortado que impede a leitura, legenda a tapar pontos ou barras, \
dados mal representados, rótulo de eixo com unidade errada.
- No máximo 4 problemas, em português europeu, concretos e acionáveis."""


# --------------------------------------------------------------------------
# Utilitários
# --------------------------------------------------------------------------
class CritiqueIssue(BaseModel):
    description: str = Field(description="Problema concreto e acionável.")
    severe: bool = Field(description="True só se viola um requisito explícito da "
                         "especificação, torna texto ilegível ou apresenta os dados de "
                         "forma errada. Questões estéticas menores: False.")


class Critique(BaseModel):
    issues: list[CritiqueIssue] = Field(description="Vazio se a figura estiver correta.")



def extract_code(text: str) -> str:
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    return (match.group(1) if match else text).strip()


def build_script(code: str, data_path: str, output_path: str) -> str:
    """Cabeçalho + código gerado: o ficheiro resultante corre sozinho a partir da raiz."""
    header = (
        "# Gerado automaticamente pelo grafo LangGraph. Correr a partir da raiz do projeto.\n"
        "from pathlib import Path\n"
        "import matplotlib\n"
        'matplotlib.use("Agg")\n'
        f"DATA_PATH = {data_path!r}\n"
        f"OUTPUT_PATH = {output_path!r}\n"
        "Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)\n\n"
    )
    return header + code + "\n"


def script_path(name: str):
    return FIGURES / "code" / f"{name}.py"


def _next_step(state: State) -> str:
    """Após um problema: voltar ao gerador ou desistir."""
    return "generator" if state.get("iteration", 0) < state.get("max_iter", 4) else "give_up"


# --------------------------------------------------------------------------
# Construção do grafo
# --------------------------------------------------------------------------
def build_graph(validators: list[Validator] | None = None, use_critic: bool = True):
    validators = validators or []

    # ---- Nó: Gerador ------------------------------------------------------
    def generator_node(state: State) -> dict:
        iteration = state.get("iteration", 0) + 1
        print(f"[{state['name']}] gerador (iteração {iteration}/{state['max_iter']})")

        user = (f"Especificação da figura:\n{state['spec']}\n\n"
                f"Descrição do dataset:\n{state['data_description']}")
        if state.get("code") and state.get("issues"):
            user += ("\n\nCódigo anterior:\n```python\n" + state["code"] + "\n```\n"
                     "Problemas a corrigir:\n- " + "\n- ".join(state["issues"]))

        try:
            resp = get_llm(0.2).invoke([SystemMessage(GEN_SYSTEM), HumanMessage(user)])
            code = extract_code(content_to_text(resp.content))
        except Exception as exc:
            return {"status": "failed", "issues": [f"Erro na API do LLM: {exc}"],
                    "iteration": iteration,
                    "log": [{"node": "generator", "iteration": iteration, "erro": str(exc)}]}

        return {"code": code, "iteration": iteration, "issues": [], "status": "running",
                "log": [{"node": "generator", "iteration": iteration, "linhas": code.count("\n") + 1}]}

    # ---- Nó: Validador (sintaxe + validadores plugáveis) ------------------
    def validator_node(state: State) -> dict:
        code, issues = state["code"], []
        try:
            compile(code, "<chart>", "exec")
        except SyntaxError as exc:
            issues.append(f"Erro de sintaxe na linha {exc.lineno}: {exc.msg}")
        if not issues:
            for validate in validators:
                try:
                    issues += validate(code)
                except Exception as exc:  # um validador avariado não deve bloquear o grafo
                    print(f"  (aviso) validador {validate.__name__} falhou: {exc}")
        print(f"[{state['name']}] validador: {len(issues)} problema(s)")
        for i in issues:
            print(f"    - {i}")
        return {"issues": issues, "stage": "validator",
                "log": [{"node": "validator", "iteration": state["iteration"], "issues": issues}]}

    # ---- Nó: Executor (subprocesso isolado) -------------------------------
    def executor_node(state: State) -> dict:
        out = ROOT / state["output_path"]
        if out.exists():
            out.unlink()
        path = script_path(state["name"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(build_script(state["code"], state["data_path"], state["output_path"]),
                        encoding="utf-8")

        issues: list[str] = []
        try:
            proc = subprocess.run([sys.executable, str(path)], cwd=ROOT,
                                  capture_output=True, text=True, timeout=180,
                                  encoding="utf-8", errors="replace")
            if proc.returncode != 0:
                issues.append("O código falhou ao executar. Traceback:\n" + proc.stderr[-1500:])
            elif not out.exists():
                issues.append("O código correu mas não gravou a figura. Usa "
                              "plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight').")
        except subprocess.TimeoutExpired:
            issues.append("O código excedeu o tempo limite de 180 s. Simplifica o processamento.")

        if issues:
            print("    " + issues[0].strip().splitlines()[-1][:300])

        print(f"[{state['name']}] executor: {'ERRO' if issues else 'OK'}")
        update = {"issues": issues, "stage": "executor",
                  "log": [{"node": "executor", "iteration": state["iteration"], "issues": issues}]}
        if not issues and not use_critic:
            update["status"] = "approved"
        return update

    # ---- Nó: Crítico visual (LLM multimodal) ------------------------------
    def critic_node(state: State) -> dict:
        out = ROOT / state["output_path"]
        b64 = base64.b64encode(out.read_bytes()).decode()
        text = (f"Especificação pedida:\n{state['spec']}\n\n"
                f"Código que gerou a figura:\n```python\n{state['code']}\n```")
        prev = state.get("last_critique") or []
        if prev:
            text += "\n\nProblemas apontados na revisão anterior:\n- " + "\n- ".join(prev)
        msg = HumanMessage(content=[
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ])
        try:
            critique = get_llm(0.0).with_structured_output(Critique).invoke(
                [SystemMessage(CRITIC_SYSTEM), msg])
            if critique is None:
                raise ValueError("resposta vazia do crítico")
        except Exception as exc:
            print(f"[{state['name']}] crítico indisponível ({exc}); figura aceite sem revisão visual")
            return {"issues": [], "status": "approved", "stage": "critic",
                    "log": [{"node": "critic", "iteration": state["iteration"], "erro": str(exc)}]}

        severe = [i.description for i in critique.issues if i.severe]
        minor = [i.description for i in critique.issues if not i.severe]
        approved = not severe
        print(f"[{state['name']}] crítico: {'APROVADA' if approved else 'REPROVADA'}")
        for i in severe:
            print(f"    - [grave] {i}")
        for i in minor:
            print(f"    - [menor, não bloqueia] {i}")
        return {"issues": severe, "last_critique": severe, "stage": "critic",
                "status": "approved" if approved else "running",
                "log": [{"node": "critic", "iteration": state["iteration"],
                         "approved": approved, "severe": severe, "minor": minor}]}

    # ---- Nó: Desistir -----------------------------------------------------
    def give_up_node(state: State) -> dict:
        status = "unapproved" if state.get("stage") == "critic" else "failed"
        print(f"[{state['name']}] limite de iterações atingido -> {status}")
        return {"status": status, "log": [{"node": "give_up", "status": status}]}

    # ---- Arestas condicionais ---------------------------------------------
    def after_generator(state: State) -> str:
        return "end" if state.get("status") == "failed" else "validator"

    def after_validator(state: State) -> str:
        return _next_step(state) if state["issues"] else "executor"

    def after_executor(state: State) -> str:
        if state["issues"]:
            return _next_step(state)
        return "critic" if use_critic else "end"

    def after_critic(state: State) -> str:
        return "end" if state["status"] == "approved" else _next_step(state)

    g = StateGraph(State)
    g.add_node("generator", generator_node)
    g.add_node("validator", validator_node)
    g.add_node("executor", executor_node)
    g.add_node("critic", critic_node)
    g.add_node("give_up", give_up_node)

    g.add_edge(START, "generator")
    g.add_conditional_edges("generator", after_generator,
                            {"validator": "validator", "end": END})
    g.add_conditional_edges("validator", after_validator,
                            {"executor": "executor", "generator": "generator", "give_up": "give_up"})
    g.add_conditional_edges("executor", after_executor,
                            {"critic": "critic", "generator": "generator",
                             "give_up": "give_up", "end": END})
    g.add_conditional_edges("critic", after_critic,
                            {"generator": "generator", "give_up": "give_up", "end": END})
    g.add_edge("give_up", END)
    return g.compile()


# --------------------------------------------------------------------------
# API de alto nível
# --------------------------------------------------------------------------
def run_chart(name: str, spec: str, data_path: str = CONCELHO_CSV,
              data_description: str = CONCELHO_DESC,
              validators: list[Validator] | None = None,
              max_iter: int = 4, use_critic: bool = True) -> State:
    """Gera uma figura. Devolve o estado final e grava figura, código e log."""
    graph = build_graph(validators, use_critic)
    final = graph.invoke(
        {"name": name, "spec": spec, "data_path": data_path,
         "data_description": data_description, "output_path": f"figures/{name}.png",
         "iteration": 0, "max_iter": max_iter, "issues": [], "status": "running", "log": []},
        config={"recursion_limit": 60},
    )

    if final.get("code"):  # guarda o código final como script autónomo
        script_path(name).parent.mkdir(parents=True, exist_ok=True)
        script_path(name).write_text(
            build_script(final["code"], data_path, final["output_path"]), encoding="utf-8")

    log_dir = FIGURES / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / f"{name}.json").write_text(json.dumps(
        {"name": name, "spec": spec, "status": final["status"],
         "iteracoes": final["iteration"], "eventos": final["log"]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{name}] estado final: {final['status']} em {final['iteration']} iteração(ões)")
    return final