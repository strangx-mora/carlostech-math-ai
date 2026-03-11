from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from sympy import *
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, 
    implicit_multiplication_application, convert_xor
)
from sympy.integrals import integrate, heurisch, meijerg
from sympy.integrals.rde import order_terms
from sympy.solvers.inequalities import solve_univariate_inequality
from sympy.calculus.util import continuous_domain
import re
from functools import wraps
import numpy as np
import traceback
import os
import time

app = Flask(__name__)

# CONFIGURAR SESSION (sesión segura de Flask)
app.secret_key = os.environ.get('SECRET_KEY', 'carlostech_math_ai_secret_2025')

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



def latex_to_sympy(latex_expr):
    """Convierte LaTeX de MathQuill a expresión SymPy"""
    try:
        expr = latex_expr.strip()
        
        # Conversiones básicas
        expr = expr.replace("^", "**")
        expr = expr.replace("{", "(").replace("}", ")")
        expr = expr.replace(" ", "")
        
        # Funciones trigonométricas
        expr = re.sub(r'\\sin\s*\(', 'sin(', expr)
        expr = re.sub(r'\\cos\s*\(', 'cos(', expr)
        expr = re.sub(r'\\tan\s*\(', 'tan(', expr)
        expr = re.sub(r'\\sqrt\s*\{', 'sqrt(', expr)
        
        # Log natural
        expr = expr.replace("\\ln", "log")
        expr = expr.replace("ln", "log")
        
        # Multiplicación implícita
        expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr)
        expr = re.sub(r'(\))(\()', r'\1*\2', expr)
        expr = re.sub(r'(\d)(\()', r'\1*\2', expr)
        expr = re.sub(r'(\))([a-zA-Z])', r'\1*\2', expr)
        
        # Limpiar símbolos especiales
        expr = expr.replace("π", "pi")
        expr = expr.replace("e", str(E))
        
        # Parsear con transformaciones
        transformations = standard_transformations + (implicit_multiplication_application,)
        result = parse_expr(expr, transformations=transformations)
        
        return result
    except Exception as e:
        raise ValueError(f"No se pudo parsear la expresión: {latex_expr}\nError: {str(e)}")

def limpiar(expr):
    """Función auxiliar para compatibilidad"""
    return latex_to_sympy(expr)


# ====================================
# GENERAR PASOS
# ====================================

def pasos_integral(expr, resultado, a=None, b=None):
    """Genera pasos detallados tipo premium (MathWay style)"""
    
    # Detectar tipo de integral
    tipo = "General"
    regla = ""
    explicacion = ""
    
    try:
        # Verificar componentes
        has_poly = expr.is_polynomial(x)
        has_sin = expr.has(sin)
        has_cos = expr.has(cos)
        has_tan = expr.has(tan)
        has_exp = expr.has(exp)
        has_log = expr.has(log)
        
        # Clasificación inteligente
        if has_sin:
            tipo = "Trigonométrica (Seno)"
            regla = "∫sin(u) du = -cos(u) + C"
            explicacion = "Usa la regla de integración trigonométrica para seno"
        elif has_cos:
            tipo = "Trigonométrica (Coseno)"
            regla = "∫cos(u) du = sin(u) + C"
            explicacion = "Usa la regla de integración trigonométrica para coseno"
        elif has_tan:
            tipo = "Trigonométrica (Tangente)"
            regla = "∫tan(u) du = -ln|cos(u)| + C"
            explicacion = "Usa la regla de integración para tangente"
        elif has_exp:
            tipo = "Exponencial"
            regla = "∫eᵘ du = eᵘ + C"
            explicacion = "Usa la regla de exponenciales"
        elif has_log:
            tipo = "Logarítmica"
            regla = "∫ln(u) du = u·ln(u) - u + C"
            explicacion = "Usa integración por partes para logaritmos"
        elif has_poly:
            tipo = "Polinómica"
            regla = "∫xⁿ dx = xⁿ⁺¹/(n+1) + C"
            explicacion = "Usa la regla de potencia para polinomios"
        else:
            tipo = "Integración Simbólica"
            regla = "Aplicando técnicas avanzadas de cálculo"
            explicacion = "Se aplican transformaciones simbólicas complejas"
    except:
        tipo = "Integración General"
        regla = "Se aplicaron técnicas de cálculo simbólico"
    
    # Construir HTML profesional
    html_pasos = ""
    
    # Paso 1: Función original
    html_pasos += "<div class='paso-premium'>"
    html_pasos += "<div class='paso-header'>📍 Paso 1: Función Original</div>"
    html_pasos += "<div class='paso-content'>$$f(x) = " + latex(expr) + "$$</div>"
    html_pasos += "</div>"
    
    # Paso 2: Clasificación
    html_pasos += "<div class='paso-premium'>"
    html_pasos += "<div class='paso-header'>🔍 Paso 2: Clasificación</div>"
    html_pasos += "<div class='paso-content'>"
    html_pasos += f"<p>{tipo}</p>"
    html_pasos += f"<p style='font-size: 0.9em; color: #94a3b8;'>{explicacion}</p>"
    html_pasos += "</div>"
    html_pasos += "</div>"
    
    # Paso 3: Regla de integración
    html_pasos += "<div class='paso-premium'>"
    html_pasos += "<div class='paso-header'>📐 Paso 3: Regla Aplicada</div>"
    html_pasos += f"<div class='paso-content'>$${regla}$$</div>"
    html_pasos += "</div>"
    
    # Paso 4: Resultado
    html_pasos += "<div class='paso-premium resultado-final'>"
    html_pasos += "<div class='paso-header'>✅ Resultado Final</div>"
    html_pasos += "<div class='paso-content'>"
    
    if a is not None and b is not None:
        try:
            a_val = float(a)
            b_val = float(b)
            html_pasos += f"<p><strong>Integral Definida:</strong></p>"
            html_pasos += f"$$\\int_{{{a_val}}}^{{{b_val}}} f(x)\\,dx = {latex(resultado)}$$"
            html_pasos += f"<p style='font-size: 0.9em; color: #94a3b8;'>Valor numérico: {float(resultado):.6f}</p>"
        except:
            html_pasos += "$$\\int f(x)\\,dx = " + latex(resultado) + "$$"
    else:
        html_pasos += "<p><strong>Integral Indefinida:</strong></p>"
        html_pasos += "$$\\int f(x)\\,dx = " + latex(resultado) + " + C$$"
        html_pasos += "<p style='font-size: 0.9em; color: #94a3b8;'>C = constante de integración arbitraria</p>"
    
    html_pasos += "</div>"
    html_pasos += "</div>"
    
    return html_pasos


# ====================================


@app.route("/resolver", methods=["POST"])
@login_required
def resolver():
    """Motor de resolución de integrales profesional"""
    data = request.json
    expr_text = data.get("integral", "").strip()
    a = data.get("a")
    b = data.get("b")
    
    if not expr_text:
        return jsonify({
            "error": "Por favor ingresa una expresión",
            "resultado": "Expresión vacía",
            "pasos": "<div class='error'>Debes ingresar una función para integrar</div>"
        }), 400
    
    try:
        # Parsear expresión
        expr = latex_to_sympy(expr_text)
        
        # Intentar resolver integral
        try:
            if a and b:
                # Integral definida
                a_val = float(a)
                b_val = float(b)
                resultado = integrate(expr, (x, a_val, b_val))
            else:
                # Integral indefinida
                resultado = integrate(expr, x)
        except Exception as e:
            return jsonify({
                "error": str(e),
                "resultado": f"❌ No se pudo integrar la expresión",
                "pasos": f"<div class='error'><p>Error: {str(e)}</p><p>Intenta con una expresión diferente</p></div>"
            }), 400
        
        # Generar pasos
        pasos = pasos_integral(expr, resultado, a, b)
        
        return jsonify({
            "resultado": f"$${latex(resultado)}$$",
            "pasos": pasos
        })
    
    except ValueError as e:
        return jsonify({
            "error": f"Error de parsing: {str(e)}",
            "resultado": "Error en la expresión",
            "pasos": f"<div class='error'><p>No se pudo interpretar la expresión matemática</p><p>{str(e)}</p></div>"
        }), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "resultado": "Error desconocido",
            "pasos": f"<div class='error'>{traceback.format_exc()}</div>"
        }), 500


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
    """Genera datos para graficar la función con manejo robusto de errores"""
    try:
        data = request.json
        expr_text = data.get("integral", "").strip()
        
        if not expr_text:
            return jsonify({"error": "Expresión vacía"}), 400
        
        # Parsear expresión
        try:
            expr = latex_to_sympy(expr_text)
        except Exception as e:
            return jsonify({"error": f"Error al parsear: {str(e)}"}), 400
        
        # Obtener límites
        a = data.get("a")
        b = data.get("b")
        
        try:
            a_val = float(a) if a else -5
            b_val = float(b) if b else 5
        except:
            a_val, b_val = -5, 5
        
        # Generar puntos para la gráfica
        x_vals = np.linspace(a_val, b_val, 400)
        y_vals = []
        
        # Compilar función para mejor rendimiento
        try:
            f = lambdify(x, expr, modules=['numpy'])
            y_vals = f(x_vals)
            
            # Convertir array a lista y manejar valores especiales
            y_list = []
            for y in y_vals:
                try:
                    y_float = float(y)
                    # Verificar si es válido
                    if np.isnan(y_float) or np.isinf(y_float):
                        y_list.append(None)
                    else:
                        y_list.append(y_float)
                except (TypeError, ValueError):
                    y_list.append(None)
            
        except Exception as e:
            # Fallback: evaluación punto a punto
            y_list = []
            for x_val in x_vals:
                try:
                    y_val = expr.subs(x, x_val)
                    y_float = float(y_val)
                    if np.isnan(y_float) or np.isinf(y_float):
                        y_list.append(None)
                    else:
                        y_list.append(y_float)
                except:
                    y_list.append(None)
        
        return jsonify({
            "x": x_vals.tolist(),
            "y": y_list,
            "a": float(a_val),
            "b": float(b_val)
        })
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error al graficar: {str(e)}"}), 400


if __name__=="__main__":

    import os

    port=int(os.environ.get("PORT",10000))

    app.run(host="0.0.0.0",port=port,debug=False)