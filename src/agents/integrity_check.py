"""Nó de integridade visual (Parte II, Fase 2; Wilke, cap. 17: tinta proporcional).

Análise estática (AST) do código gerado: rejeita gráficos de barras cujo eixo métrico
não parte de zero, forçando o gerador a reescrever o código no grafo.
"""
import ast

_LIMIT_FUNCS = {"set_ylim": "y", "ylim": "y", "set_ybound": "y",
                "set_xlim": "x", "xlim": "x", "set_xbound": "x"}
_LOWER_KW = {"bottom", "left", "ymin", "xmin", "lower"}
_RULE = ("Esta regra de integridade (barras com eixo métrico a partir de zero) tem "
         "prioridade sobre a especificação.")


def _fn(call: ast.Call) -> str:
    f = call.func
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""


def _kw(call: ast.Call, name: str):
    return next((k.value for k in call.keywords if k.arg == name), None)


def _str(node) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _is_true(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _find_bars(tree) -> list[dict]:
    """Gráficos de barras e o respetivo eixo métrico ('x', 'y' ou 'xy' se desconhecido)."""
    bars = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn, axis, base_kw = _fn(n), None, None
        if fn == "bar":
            axis, base_kw = "y", "bottom"
        elif fn == "barh":
            axis, base_kw = "x", "left"
        elif fn == "barplot":                                  # seaborn
            orient = _str(_kw(n, "orient"))
            axis = ("x" if orient in ("h", "y", "horizontal")
                    else "y" if orient in ("v", "x", "vertical") else "xy")
        elif fn == "plot" and _str(_kw(n, "kind")) in ("bar", "barh"):
            axis = "x" if _str(_kw(n, "kind")) == "barh" else "y"
        if axis is None:
            continue
        bars.append({"line": n.lineno, "axis": axis, "log": _is_true(_kw(n, "log")),
                     "base": _kw(n, base_kw) if base_kw else None})
    return bars


def _limits(tree) -> list[tuple]:
    """(linha, eixo, expressão do limite inferior) de todas as chamadas que fixam limites."""
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = _fn(n)
        if fn in _LIMIT_FUNCS:
            lower = None
            if n.args:
                a0 = n.args[0]
                lower = a0.elts[0] if isinstance(a0, (ast.List, ast.Tuple)) and a0.elts else a0
            for k in n.keywords:
                if k.arg in _LOWER_KW:
                    lower = k.value
            out.append((n.lineno, _LIMIT_FUNCS[fn], lower))
        elif (fn == "axis" and n.args and isinstance(n.args[0], (ast.List, ast.Tuple))
              and len(n.args[0].elts) == 4):
            e = n.args[0].elts
            out += [(n.lineno, "x", e[0]), (n.lineno, "y", e[2])]
        for k in n.keywords:                                    # df.plot(ylim=(a, b)), ax.set(xlim=...)
            if k.arg in ("xlim", "ylim") and isinstance(k.value, (ast.Tuple, ast.List)) and k.value.elts:
                out.append((n.lineno, k.arg[0], k.value.elts[0]))
    return out


def _log_axes(tree) -> list[tuple]:
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = _fn(n)
        if (fn in ("set_yscale", "yscale", "set_xscale", "xscale")
                and n.args and _str(n.args[0]) in ("log", "symlog")):
            out.append((n.lineno, "y" if "yscale" in fn else "x"))
        for k in n.keywords:
            if k.arg in ("xscale", "yscale") and _str(k.value) in ("log", "symlog"):
                out.append((n.lineno, k.arg[0]))
    return out

def _is_negative(expr) -> bool:
    """True se a expressão é negativa por construção: -x, -x * k, k * -x, -x / k."""
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
        return True
    if isinstance(expr, ast.BinOp):
        if isinstance(expr.op, ast.Mult):
            return _is_negative(expr.left) != _is_negative(expr.right)  # dois sinais menos dão positivo
        if isinstance(expr.op, ast.Div):
            return _is_negative(expr.left)
    return False

def _lower_problem(expr) -> str | None:
    """None se o limite inferior é aceitável; caso contrário, o motivo."""
    if expr is None:
        return None
    if isinstance(expr, ast.Constant):
        if expr.value is None:
            return None
        if isinstance(expr.value, (int, float)):
            return None if expr.value <= 0 else f"o limite inferior é {expr.value}, maior do que zero"
    if _is_negative(expr):
        return None                                             # limite negativo: a base 0 fica dentro do eixo
    return "o limite inferior é uma expressão calculada (por exemplo, min() * 0.9) e não 0"


def count_bar_charts(code: str) -> int:
    try:
        return len(_find_bars(ast.parse(code)))
    except SyntaxError:
        return 0


def bar_axis_findings(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []                                               # a sintaxe é validada noutro passo
    bars = _find_bars(tree)
    if not bars:
        return []
    limits, logs = _limits(tree), _log_axes(tree)
    found: list[str] = []
    for b in bars:
        axes = ("x", "y") if b["axis"] == "xy" else (b["axis"],)
        if b["log"]:
            found.append(f"Linha {b['line']}: barras com log=True; uma escala logarítmica não tem zero. "
                         "Usa escala linear com base em 0 (ou um dot plot).")
        base = b["base"]
        if isinstance(base, ast.Constant) and isinstance(base.value, (int, float)) and base.value != 0:
            found.append(f"Linha {b['line']}: a base das barras ({base.value}) não é zero.")
        for line, ax, lower in limits:
            if ax in axes and (problem := _lower_problem(lower)):
                found.append(f"Linha {line}: o eixo {ax} (métrico) de um gráfico de barras não começa "
                             f"em zero ({problem}). Barras truncadas distorcem as magnitudes (Wilke, "
                             f"cap. 17). Define o limite inferior como 0, por exemplo ax.set_{ax}lim(0, ...).")
        for line, ax in logs:
            if ax in axes:
                found.append(f"Linha {line}: escala logarítmica no eixo {ax} (métrico) de um gráfico de "
                             "barras; a base não é zero. Usa escala linear a partir de 0.")
    return list(dict.fromkeys(found))


def check_bar_axis_integrity(code: str) -> list[str]:
    """Validador para o grafo: lista de problemas (vazia se o código cumpre a regra)."""
    found = bar_axis_findings(code)
    return found + [_RULE] if found else []