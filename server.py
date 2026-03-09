from flask import Flask, request, jsonify, render_template
from sympy import *
from sympy.parsing.sympy_parser import parse_expr
import re

app = Flask(__name__)

x = symbols('x')

# -----------------------------
# LIMPIAR EXPRESION
# -----------------------------

def limpiar(expr):

    expr = expr.replace("^","**")

    expr = expr.replace("{","(")
    expr = expr.replace("}",")")

    expr = expr.replace("sin","sin")
    expr = expr.replace("cos","cos")
    expr = expr.replace("tan","tan")

    expr = expr.replace("ln","log")

    expr = re.sub(r'(\d)x', r'\1*x', expr)

    return expr


# -----------------------------
# GENERAR PASOS
# -----------------------------

def pasos_integral(expr,resultado):

    pasos=[]

    pasos.append("<b>Paso 1:</b> Identificar la función")

    pasos.append(f"$$ f(x) = {latex(expr)} $$")

    pasos.append("<b>Paso 2:</b> Aplicar reglas de integración")

    if expr.is_polynomial():

        pasos.append("Se usa la regla de potencia")

        pasos.append("$$ \\int x^n dx = \\frac{x^{n+1}}{n+1} $$")

    elif expr.has(sin) or expr.has(cos):

        pasos.append("Se usan integrales trigonométricas")

    elif expr.has(log):

        pasos.append("Se usan reglas logarítmicas")

    elif expr.has(exp):

        pasos.append("Se aplica la integral exponencial")

    else:

        pasos.append("Se aplica integración simbólica general")

    pasos.append("<b>Resultado:</b>")

    pasos.append(f"$$ {latex(resultado)} $$")

    return "<br>".join(pasos)


# -----------------------------
# PAGINA
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# RESOLVER INTEGRAL
# -----------------------------

@app.route("/resolver", methods=["POST"])
def resolver():

    data=request.json

    expr_text=data.get("integral")

    a=data.get("a")
    b=data.get("b")

    try:

        expr_text=limpiar(expr_text)

        expr=parse_expr(expr_text)

        # INTEGRAL DEFINIDA

        if a and b:

            resultado=integrate(expr,(x,float(a),float(b)))

        # INDEFINIDA

        else:

            resultado=integrate(expr,x)

        pasos=pasos_integral(expr,resultado)

        return jsonify({

            "resultado":f"$$ {latex(resultado)} $$",

            "pasos":pasos

        })

    except Exception as e:

        return jsonify({

            "resultado":"No se pudo resolver",

            "pasos":str(e)

        })


# -----------------------------
# DERIVADA
# -----------------------------

@app.route("/derivada",methods=["POST"])
def derivada():

    data=request.json

    expr_text=limpiar(data.get("expresion"))

    try:

        expr=parse_expr(expr_text)

        resultado=diff(expr,x)

        return jsonify({

            "resultado":f"$$ {latex(resultado)} $$"

        })

    except:

        return jsonify({

            "resultado":"Error en derivada"

        })


if __name__=="__main__":

    import os

    port=int(os.environ.get("PORT",10000))

    app.run(host="0.0.0.0",port=port)