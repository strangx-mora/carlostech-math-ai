from flask import Flask, request, jsonify, render_template
from sympy import *
from sympy.parsing.latex import parse_latex

app = Flask(__name__)

x = symbols('x')


# -----------------------------
# DETECTAR METODO
# -----------------------------

def detectar_metodo(expr):

    if expr.is_Pow:
        return "regla_potencia"

    if expr.is_Add:
        return "linealidad"

    if expr.is_Mul:
        return "partes"

    if expr.has(sin) or expr.has(cos) or expr.has(tan):
        return "trig"

    if expr.has(exp):
        return "exponencial"

    return "general"


# -----------------------------
# GENERAR PASOS
# -----------------------------

def generar_pasos(expr, resultado):

    metodo = detectar_metodo(expr)

    pasos = []

    pasos.append("<b>Paso 1: Identificar la función</b>")
    pasos.append(f"$$f(x) = {latex(expr)}$$")

    if metodo == "regla_potencia":

        pasos.append("<b>Paso 2: Aplicar regla de potencia</b>")
        pasos.append("$$ \\int x^n dx = \\frac{x^{n+1}}{n+1} $$")

    elif metodo == "linealidad":

        pasos.append("<b>Paso 2: Separar la integral</b>")
        pasos.append("$$ \\int (a+b)dx = \\int a dx + \\int b dx $$")

    elif metodo == "partes":

        pasos.append("<b>Paso 2: Usar integración por partes</b>")
        pasos.append("$$ \\int u dv = uv - \\int v du $$")

    elif metodo == "trig":

        pasos.append("<b>Paso 2: Usar identidades trigonométricas</b>")

    elif metodo == "exponencial":

        pasos.append("<b>Paso 2: Usar integral exponencial</b>")
        pasos.append("$$ \\int e^x dx = e^x $$")

    else:

        pasos.append("<b>Paso 2: Aplicar integración simbólica</b>")

    pasos.append("<b>Paso final: Resultado</b>")
    pasos.append(f"$$ {latex(resultado)} $$")

    return "<br>".join(pasos)


# -----------------------------
# PAGINA PRINCIPAL
# -----------------------------

@app.route("/", methods=["GET","POST"])
def home():
    return render_template("index.html")


# -----------------------------
# RESOLVER INTEGRAL
# -----------------------------

@app.route("/resolver", methods=["POST"])
def resolver():

    data = request.json

    latex_expr = data.get("integral")

    limite_inferior = data.get("a")
    limite_superior = data.get("b")

    try:

        expr = parse_latex(latex_expr)

        # INTEGRAL DEFINIDA
        if limite_inferior and limite_superior:

            a = float(limite_inferior)
            b = float(limite_superior)

            resultado = integrate(expr, (x, a, b))

            pasos = generar_pasos(expr, resultado)

            return jsonify({
                "tipo": "definida",
                "resultado": f"$$ {latex(resultado)} $$",
                "pasos": pasos
            })

        # INTEGRAL INDEFINIDA
        else:

            resultado = integrate(expr, x)

            pasos = generar_pasos(expr, resultado)

            return jsonify({
                "tipo": "indefinida",
                "resultado": f"$$ {latex(resultado)} + C $$",
                "pasos": pasos
            })

    except Exception as e:

        return jsonify({
            "resultado": "No se pudo resolver",
            "pasos": str(e)
        })


# -----------------------------
# DERIVADAS
# -----------------------------

@app.route("/derivada", methods=["POST"])
def derivada():

    data = request.json
    latex_expr = data.get("expresion")

    try:

        expr = parse_latex(latex_expr)

        resultado = diff(expr, x)

        return jsonify({
            "resultado": f"$$ {latex(resultado)} $$"
        })

    except:

        return jsonify({
            "resultado": "Error"
        })


# -----------------------------
# LIMITES
# -----------------------------

@app.route("/limite", methods=["POST"])
def limite():

    data = request.json

    latex_expr = data.get("expresion")
    valor = data.get("valor")

    try:

        expr = parse_latex(latex_expr)

        resultado = limit(expr, x, float(valor))

        return jsonify({
            "resultado": f"$$ {latex(resultado)} $$"
        })

    except:

        return jsonify({
            "resultado": "Error"
        })


if __name__ == "__main__":
    app.run(debug=True)