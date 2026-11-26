"""Testa o nó de integridade com 10 trechos de código conhecidos."""
from agents.integrity_check import check_bar_axis_integrity

CASOS = [
    ("barras com set_ylim(80, 100)", "ax.bar(x, y)\nax.set_ylim(80, 100)\n", True),
    ("barh com limite = min()*0.9", "ax.barh(c, v)\nax.set_xlim(df['v'].min() * 0.9, df['v'].max())\n", True),
    ("barras com set_ylim(0, max*1.15)", "ax.bar(x, y)\nax.set_ylim(0, y.max() * 1.15)\n", False),
    ("barh divergente, limites simétricos", "ax.barh(c, v)\nax.set_xlim(-m * 1.25, m * 1.25)\n", False),
    ("barras com escala log", "ax.bar(x, y)\nplt.yscale('log')\n", True),
    ("linhas com ylim truncado (sem barras)", "ax.plot(t, s)\nax.set_ylim(3000, 5000)\n", False),
    ("barras com bottom=50", "ax.bar(x, h, bottom=50)\n", True),
    ("sns.barplot com plt.ylim(min*0.95)", "sns.barplot(data=df, x='a', y='b')\nplt.ylim(df['b'].min() * 0.95, None)\n", True),
    ("barras empilhadas (bottom variável)", "ax.bar(x, a)\nax.bar(x, b, bottom=a)\n", False),
    ("barras com xlim no eixo das categorias", "ax.bar(x, y)\nax.set_xlim(-0.5, 4.5)\n", False),
]

certos = 0
for titulo, codigo, esperado_rejeitar in CASOS:
    problemas = check_bar_axis_integrity(codigo)
    rejeitou = bool(problemas)
    ok = rejeitou == esperado_rejeitar
    certos += ok
    print(f"[{'CORRETO' if ok else 'INCORRETO'}] {titulo}: "
          f"{'REPROVADO' if rejeitou else 'APROVADO'} (esperado: {'REPROVADO' if esperado_rejeitar else 'APROVADO'})")
    for p in problemas[:-1]:
        print("      *", p)
print(f"\n{certos}/{len(CASOS)} casos corretos")