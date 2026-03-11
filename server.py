from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from sympy import *
from sympy.parsing.sympy_parser import parse_expr
import re
from functools import wraps

app = Flask(__name__)

# CONFIGURAR SESSION (sesión segura de Flask)
app.secret_key = 'carlostech_math_ai_secret_2025'

# USUARIOS DE PRUEBA (en una app real, usar base de datos)
USERS = {
    'carlos': 'carlos123',
    'admin': 'admin123',
    'demo': 'demo123'
}

x = symbols('x')

# ====================================
# DECORADOR PARA PROTEGER RUTAS
# ====================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            # Para APIs (JSON), retornar error JSON; para páginas, redirigir
            if request.is_json or request.path.startswith('/resolver') or request.path.startswith('/graficar') or request.path.startswith('/derivada'):
                return jsonify({"error": "No estás autenticado"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ====================================
# RUTAS DE AUTENTICACIÓN
# ====================================

@app.route("/", methods=["GET", "POST"])
def login():
    """Página de inicio - Login"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        # Validar credenciales
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")
    
    # Si ya está logueado, redirigir a la app
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    return render_template("login.html")


@app.route("/app")
@login_required
def dashboard():
    """Página principal de la aplicación"""
    return render_template("index.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))  # Redirige a "/" que es la función login()

# ====================================
# FUNCIONES AUXILIARES
# ====================================



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

def pasos_integral(expr, resultado, a=None, b=None):
    """Genera pasos detallados tipo premium"""
    pasos = []
    
    # Clasificar tipo
    if expr.is_polynomial():
        tipo = 'Polinómica'
        regla = '∫xⁿ dx = xⁿ⁺¹/(n+1) + C'
    elif expr.has(sin):
        tipo = 'Trigonométrica (Seno)'
        regla = '∫sin(x) dx = -cos(x) + C'
    elif expr.has(cos):
        tipo = 'Trigonométrica (Coseno)'
        regla = '∫cos(x) dx = sin(x) + C'
    elif expr.has(exp):
        tipo = 'Exponencial'
        regla = '∫eˣ dx = eˣ + C'
    elif expr.has(log):
        tipo = 'Logarítmica'
        regla = '∫ln(x) dx = x·ln(x) - x + C'
    else:
        tipo = 'General'
        regla = 'Integración simbólica'
    
    # Construir HTML
    html_pasos = ""
    html_pasos += "<div class='paso-premium'><h3>🔍 Tipo</h3><p>" + tipo + "</p></div>"
    html_pasos += "<div class='paso-premium'><h3>📝 Función</h3>$$f(x) = " + latex(expr) + "$$</div>"
    html_pasos += "<div class='paso-premium'><h3>📐 Regla</h3>$$" + regla + "$$</div>"
    
    html_pasos += "<div class='paso-premium resultado-final'>"
    html_pasos += "<h3>✅ Resultado</h3>"
    
    if a is not None and b is not None:
        html_pasos += "$$\\int_{" + latex(a) + "}^{" + latex(b) + "} f(x)\\,dx = " + latex(resultado) + "$$"
        html_pasos += "<p class='desc'>Integral definida evaluada</p>"
    else:
        html_pasos += "$$\\int f(x)\\,dx = " + latex(resultado) + " + C$$"
        html_pasos += "<p class='desc'>C = constante de integración</p>"
    
    html_pasos += "</div>"
    
    return html_pasos


# -----------------------------
# PAGINA
# -----------------------------


# -----------------------------
# RESOLVER INTEGRAL
# -----------------------------

@app.route("/resolver", methods=["POST"])
@login_required
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

        pasos=pasos_integral(expr, resultado, a, b)

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
@login_required
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


# ============================
# GRAFICAR FUNCIÓN
# ============================

@app.route("/graficar", methods=["POST"])
@login_required
def graficar():
    """Genera datos para graficar la función"""
    try:
        data = request.json
        expr_text = limpiar(data.get("integral", ""))
        a = data.get("a")
        b = data.get("b")
        
        if not expr_text:
            return jsonify({"error": "Expresión vacía"}), 400
        
        expr = parse_expr(expr_text)
        
        # Definir rango de x
        if a and b:
            x_min, x_max = float(a), float(b)
        else:
            x_min, x_max = -5, 5
        
        # Generar puntos para la gráfica
        import numpy as np
        x_vals = np.linspace(x_min, x_max, 300)
        
        # Crear función de evaluación
        f = lambdify(x, expr, 'numpy')
        
        try:
            y_vals = f(x_vals)
        except:
            # Si hay error, usar evaluación más cautelosa
            y_vals = []
            for x_val in x_vals:
                try:
                    y_val = expr.subs(x, x_val)
                    y_vals.append(float(y_val))
                except:
                    y_vals.append(None)
        
        return jsonify({
            "x": x_vals.tolist(),
            "y": [float(val) if val is not None else None for val in y_vals],
            "a": float(a) if a else None,
            "b": float(b) if b else None
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__=="__main__":

    import os

    port=int(os.environ.get("PORT",10000))

    app.run(host="0.0.0.0",port=port,debug=False)