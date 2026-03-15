import sys
sys.stdout.reconfigure(encoding='utf-8')

from server import IntegralSolver
from sympy import latex

tests = [
    # Basicas
    ("x",               True),
    ("2x",              True),
    ("x**2",            True),
    ("3*x**4 - 2*x + 1",True),
    # Trig
    ("sin(x)",          True),
    ("cos(x)",          True),
    ("tan(x)",          True),
    ("sin(x)**2",       True),
    ("sin(x)*cos(x)",   True),
    # Exponencial
    ("exp(x)",          True),
    ("exp(2*x)",        True),
    ("x*exp(x)",        True),
    # Log
    ("log(x)",          True),
    ("1/x",             True),
    ("x*log(x)",        True),
    # Radicales
    ("sqrt(x)",         True),
    ("1/sqrt(x)",       True),
    ("sqrt(1-x**2)",    True),
    ("x/sqrt(x**2+1)",  True),
    # Racionales
    ("1/(x**2+1)",      True),
    ("1/(x*(x+1))",     True),
    ("(x+1)/(x**2+1)",  True),
    # Por partes
    ("x*sin(x)",        True),
    ("x**2*sin(x)",     True),
    ("x*cos(x)",        True),
    ("x**2*exp(x)",     True),
    # Hiperbolicas
    ("sinh(x)",         True),
    ("cosh(x)",         True),
    # Trig inversas
    ("asin(x)",         True),
    ("atan(x)",         True),
    # LaTeX de MathQuill
    ("\\sin(x)",        True),
    ("\\cos(x)",        True),
    ("\\frac{1}{x}",    True),
    ("\\sqrt{x}",       True),
    ("x^{2}",           True),
    ("2x^{3}",          True),
]

ok = 0
fail = 0
for expr, expected in tests:
    s = IntegralSolver(expr)
    success = s.solve()
    status = "OK  " if success else "FAIL"
    result_str = latex(s.result)[:45] if success else str(s.errors)[:45]
    print(f"{status} | {expr:30s} | {result_str}")
    if success:
        ok += 1
    else:
        fail += 1

print(f"\nTotal: {ok} OK / {fail} FAIL de {len(tests)}")
