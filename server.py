"""
MOTOR MATEMÁTICO PROFESIONAL DE INTEGRALES
Similar a Mathway/Wolfram Alpha
Creado para CarlosTech Math AI
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from sympy import *
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, 
    implicit_multiplication_application, convert_xor
)
from sympy.integrals import integrate as sympy_integrate
from sympy.integrals.heurisch import heurisch
import re
from functools import wraps
import numpy as np
import traceback
import os
import time
from datetime import datetime

app = Flask(__name__)

# CONFIGURAR SESSION
app.secret_key = os.environ.get('SECRET_KEY', 'carlostech_math_ai_secret_2025')

# USUARIOS
USERS = {
    'carlos': 'carlos123',
    'admin': 'admin123',
    'demo': 'demo123'
}

x = symbols('x')

# ====================================
# MOTOR MATEMÁTICO AVANZADO
# ====================================

class IntegralSolver:
    """Motor avanzado de resolución de integrales con múltiples métodos"""
    
    def __init__(self, expr_str, var='x', limits=None):
        self.expr_str = expr_str
        self.var = Symbol(var)
        self.limits = limits
        self.expr = None
        self.simplified_expr = None
        self.result = None
        self.method_detected = None
        self.steps = []
        self.errors = []
        self.start_time = time.time()
        
    def parse_input(self):
        """Parse varios formatos de entrada"""
        try:
            expr_text = self.expr_str.strip()
            
            # Eliminar ∫ y dx si existen
            expr_text = re.sub(r'∫\s*', '', expr_text)
            expr_text = re.sub(r'd[a-zA-Z]\s*$', '', expr_text)
            
            # Conversiones básicas
            expr_text = expr_text.replace("^", "**")
            expr_text = expr_text.replace("{", "(").replace("}", ")")
            
            # LaTeX a sympy
            expr_text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', expr_text)
            expr_text = re.sub(r'\\sin\s*\(', 'sin(', expr_text)
            expr_text = re.sub(r'\\cos\s*\(', 'cos(', expr_text)
            expr_text = re.sub(r'\\tan\s*\(', 'tan(', expr_text)
            expr_text = re.sub(r'\\sqrt\s*\{', 'sqrt(', expr_text)
            expr_text = re.sub(r'\\log\s*\(', 'log(', expr_text)
            expr_text = expr_text.replace("\\ln", "log")
            expr_text = expr_text.replace("ln", "log")
            expr_text = expr_text.replace("π", "pi")
            expr_text = expr_text.replace("e", "E")
            expr_text = expr_text.replace("∞", "oo")
            
            # Espacios
            expr_text = expr_text.replace(" ", "")
            
            # Parse con transformaciones
            transformations = (
                standard_transformations + 
                (implicit_multiplication_application, convert_xor)
            )
            self.expr = parse_expr(expr_text, local_dict={'E': E}, transformations=transformations)
            self.steps.append(f"✓ Expresión parseada: ${latex(self.expr)}$")
            return True
            
        except Exception as e:
            self.errors.append(f"Error en parsing: {str(e)}")
            return False
    
    def simplify_expr(self):
        """Simplificar expresión inicial"""
        try:
            # Intentar expansión primero
            expanded = expand(self.expr)
            simplified = simplify(expanded)
            
            self.simplified_expr = simplified
            if simplified != self.expr:
                self.steps.append(
                    f"✓ Simplificación: ${latex(self.expr)}$ → ${latex(self.simplified_expr)}$"
                )
                self.expr = self.simplified_expr
            return True
        except Exception as e:
            self.errors.append(f"Error en simplificación: {str(e)}")
            return False
    
    def analyze_integral_type(self):
        """Analiza y detecta el tipo de integral"""
        try:
            expr = self.expr
            
            análisis = {
                'is_polynomial': expr.is_polynomial(self.var),
                'has_sin': expr.has(sin),
                'has_cos': expr.has(cos),
                'has_tan': expr.has(tan),
                'has_exp': expr.has(exp),
                'has_log': expr.has(log),
                'has_sqrt': expr.has(sqrt),
                'has_rational': any(arg.is_rational for arg in expr.free_symbols if isinstance(arg, (Rational, Float))),
                'degree': degree(expr, self.var) if expr.is_polynomial(self.var) else None,
            }
            
            return análisis
        except:
            return {}
    
    def detect_method(self):
        """Detecta automáticamente el método de integración"""
        try:
            análisis = self.analyze_integral_type()
            expr = self.expr
            
            # Polinómica
            if análisis.get('is_polynomial'):
                self.method_detected = "Regla de Potencia (Polinómica)"
                self.steps.append(f"📊 Método: Regla de potencia: ∫xⁿ dx = (xⁿ⁺¹)/(n+1) + C")
                return "polynomial"
            
            # Seno solo
            elif análisis.get('has_sin') and not análisis.get('has_cos'):
                self.method_detected = "Función Trigonométrica - Seno"
                self.steps.append(f"🔢 Método: ∫sin(x) dx = -cos(x) + C")
                return "trig_sin"
            
            # Coseno solo
            elif análisis.get('has_cos') and not análisis.get('has_sin'):
                self.method_detected = "Función Trigonométrica - Coseno"
                self.steps.append(f"🔢 Método: ∫cos(x) dx = sin(x) + C")
                return "trig_cos"
            
            # Tangente
            elif análisis.get('has_tan'):
                self.method_detected = "Función Trigonométrica - Tangente"
                self.steps.append(f"🔢 Método: ∫tan(x) dx = -ln|cos(x)| + C")
                return "trig_tan"
            
            # Trigonométricas mixtas
            elif análisis.get('has_sin') and análisis.get('has_cos'):
                self.method_detected = "Trigonometría Mixta (Identidades)"
                self.steps.append(f"🔢 Método: Usar identidades trigonométricas")
                return "trig_mixed"
            
            # Exponencial
            elif análisis.get('has_exp') and not expr.is_polynomial(self.var):
                self.method_detected = "Función Exponencial"
                self.steps.append(f"📈 Método: ∫eˣ dx = eˣ + C")
                return "exponential"
            
            # Logarítmica
            elif análisis.get('has_log'):
                self.method_detected = "Logarítmica (Integración por Partes)"
                self.steps.append(f"📝 Método: Integración por partes")
                return "logarithmic"
            
            # Raíces
            elif análisis.get('has_sqrt'):
                self.method_detected = "Raíces (Sustitución Trigonométrica)"
                self.steps.append(f"🔄 Método: Sustitución trigonométrica")
                return "radical"
            
            else:
                self.method_detected = "Integración Simbólica General"
                self.steps.append(f"🔍 Método: Análisis simbólico avanzado")
                return "general"
                
        except Exception as e:
            self.errors.append(f"Error en detección: {str(e)}")
            self.method_detected = "General"
            return "general"
    
    def solve_integral(self):
        """Resuelve la integral usando múltiples estrategias"""
        try:
            method_type = self.detect_method()
            
            result = None
            
            # Estrategia 1: Integración directa de SymPy (más rápido)
            try:
                if self.limits:
                    a, b = self.limits
                    result = sympy_integrate(self.expr, (self.var, float(a), float(b)))
                    self.steps.append(f"✓ Aplicando integración definida")
                else:
                    result = sympy_integrate(self.expr, self.var, meijerg=False)
                    self.steps.append(f"✓ Aplicando integración indefinida")
                
                if result is not None and result != oo and result != -oo:
                    self.result = result
                    return True
            except Exception as e:
                pass
            
            # Estrategia 2: Método heurístico
            if result is None:
                try:
                    result = heurisch(self.expr, self.var)
                    if result is not None:
                        self.steps.append("✓ Usando método heurístico avanzado")
                        self.result = result
                        return True
                except:
                    pass
            
            # Estrategia 3: Integración por partes manual
            if result is None and method_type in ['logarithmic']:
                try:
                    result = self._integration_by_parts()
                    if result:
                        self.steps.append("✓ Aplicando integración por partes")
                        self.result = result
                        return True
                except:
                    pass
            
            # Estrategia 4: Sustituciones comunes
            if result is None and method_type in ['radical']:
                try:
                    result = self._try_substitutions()
                    if result:
                        self.steps.append("✓ Aplicando sustitución trigonométrica")
                        self.result = result
                        return True
                except:
                    pass
            
            # Estrategia 5: Fracciones parciales
            if result is None and method_type == 'general':
                try:
                    result = self._partial_fractions()
                    if result:
                        self.steps.append("✓ Usando descomposición en fracciones parciales")
                        self.result = result
                        return True
                except:
                    pass
            
            if result is not None:
                self.result = result
                return True
            else:
                self.errors.append("❌ No se pudo determinar una solución con los métodos disponibles")
                return False
                
        except Exception as e:
            self.errors.append(f"Error crítico: {str(e)}")
            traceback.print_exc()
            return False
    
    def _integration_by_parts(self):
        """Integración por partes: ∫u dv = uv - ∫v du"""
        try:
            # Para expresiones como x*sin(x), x*exp(x), etc.
            mul_terms = Add.make_args(self.expr)
            
            for term in mul_terms:
                args = Mul.make_args(term)
                if len(args) >= 2:
                    # Intentar asignar u y dv
                    for i, arg in enumerate(args):
                        if not arg.is_constant(self.var):
                            u = arg
                            dv = Mul(*[a for j, a in enumerate(args) if j != i])
                            du = diff(u, self.var)
                            v = sympy_integrate(dv, self.var)
                            if v is not None:
                                result = u * v - sympy_integrate(v * du, self.var)
                                return result
            
            return None
        except:
            return None
    
    def _try_substitutions(self):
        """Intenta sustituciones trigonométricas comunes"""
        try:
            # sqrt(1-x^2): x = sin(u)
            if self.expr.has(sqrt(1 - self.var**2)):
                u = Symbol('u')
                sub = self.expr.subs(self.var, sin(u)) * cos(u)
                integral = sympy_integrate(sub, u)
                return integral.subs(u, asin(self.var))
            
            # sqrt(x^2+1): x = tan(u)
            if self.expr.has(sqrt(self.var**2 + 1)):
                u = Symbol('u')
                sub = self.expr.subs(self.var, tan(u)) * sec(u)**2
                integral = sympy_integrate(sub, u)
                return integral.subs(u, atan(self.var))
            
            # sqrt(x^2-1): x = sec(u)
            if self.expr.has(sqrt(self.var**2 - 1)):
                u = Symbol('u')
                sub = self.expr.subs(self.var, sec(u)) * sec(u)*tan(u)
                integral = sympy_integrate(sub, u)
                return integral.subs(u, asec(self.var))
            
            return None
        except:
            return None
    
    def _partial_fractions(self):
        """Descomposición en fracciones parciales"""
        try:
            # Para funciones racionales
            if self.expr.has(1/self.var) or isinstance(self.expr, (Add, Mul)):
                apart_expr = apart(self.expr, self.var)
                result = sympy_integrate(apart_expr, self.var)
                return result
            return None
        except:
            return None
    
    def simplify_result(self):
        """Simplifica el resultado final"""
        try:
            if self.result is not None:
                # Intentar diferentes simplificaciones
                simplified = simplify(self.result)
                expanded = expand(simplified)
                
                if len(str(simplified)) < len(str(self.result)):
                    self.steps.append(f"✓ Simplificación final")
                    self.result = simplified
                
                return True
        except Exception as e:
            pass
        
        return True
    
    def solve(self):
        """Ejecuta el proceso completo"""
        try:
            if not self.parse_input():
                return False
            
            if not self.simplify_expr():
                return False
            
            if not self.solve_integral():
                return False
            
            self.simplify_result()
            
            return True
        except Exception as e:
            self.errors.append(f"Error general: {str(e)}")
            return False
    
    def get_latex(self):
        """Retorna latex de expresiones"""
        return {
            "input": latex(self.expr) if self.expr else "",
            "result": latex(self.result) if self.result else ""
        }
    
    def get_response(self):
        """Retorna respuesta en formato JSON profesional"""
        success = self.result is not None and len(self.errors) == 0
        
        return {
            "input": latex(self.expr) if self.expr else self.expr_str,
            "simplified_expression": latex(self.simplified_expr) if self.simplified_expr else "",
            "method_detected": self.method_detected or "Desconocido",
            "steps": self.steps,
            "result": latex(self.result) if self.result else "No se pudo resolver",
            "latex": self.get_latex(),
            "success": success,
            "errors": self.errors,
            "computation_time": f"{(time.time() - self.start_time):.3f}s"
        }


def login_required(f):
    """Decorador para proteger rutas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"error": "No autenticado"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ====================================
# RUTAS DE AUTENTICACIÓN
# ====================================

@app.route("/", methods=["GET", "POST"])
def login():
    """Página de login"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", error="Credenciales inválidas")
    
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    return render_template("login.html")


@app.route("/app")
@login_required
def dashboard():
    """Dashboard principal"""
    return render_template("index.html")


@app.route("/logout")
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))


# ====================================
# API REST AVANZADA
# ====================================

@app.route("/api/resolver", methods=["POST"])
@login_required
def resolver():
    """API para resolver integrales - Motor Profesional"""
    try:
        data = request.json or {}
        expr_text = data.get("integral", "").strip()
        a = data.get("a")
        b = data.get("b")
        
        if not expr_text:
            return jsonify({
                "success": False,
                "error": "Expresión vacía",
                "steps": []
            }), 400
        
        # Crear límites si existen
        limits = None
        if a is not None and b is not None:
            try:
                limits = (float(a), float(b))
            except:
                pass
        
        # Resolver usando el motor avanzado
        solver = IntegralSolver(expr_text, var='x', limits=limits)
        
        if solver.solve():
            return jsonify(solver.get_response()), 200
        else:
            return jsonify(solver.get_response()), 400
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Error del servidor: {str(e)}",
            "steps": []
        }), 500


@app.route("/resolver", methods=["POST"])
@login_required
def resolver_legacy():
    """Endpoint legado para compatibilidad"""
    return resolver()


@app.route("/api/graficar", methods=["POST"])
@login_required
def graficar():
    """API para generar gráficos"""
    try:
        data = request.json or {}
        expr_text = data.get("integral", "").strip()
        
        if not expr_text:
            return jsonify({"error": "Expresión vacía"}), 400
        
        # Parsear expresión
        try:
            expr = parse_expr(expr_text.replace("^", "**").replace(" ", ""),
                            transformations=standard_transformations + (implicit_multiplication_application,))
        except Exception as e:
            return jsonify({"error": f"Error en parsing: {str(e)}"}), 400
        
        # Obtener límites
        a = data.get("a")
        b = data.get("b")
        
        try:
            a_val = float(a) if a else -5
            b_val = float(b) if b else 5
        except:
            a_val, b_val = -5, 5
        
        # Generar puntos
        x_vals = np.linspace(a_val, b_val, 400)
        y_list = []
        
        # Evaluar función
        try:
            f = lambdify(x, expr, modules=['numpy'])
            y_vals = f(x_vals)
            
            for y in y_vals:
                try:
                    y_float = float(y)
                    if np.isnan(y_float) or np.isinf(y_float):
                        y_list.append(None)
                    else:
                        y_list.append(y_float)
                except:
                    y_list.append(None)
        
        except:
            # Fallback punto a punto
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
        return jsonify({"error": f"Error: {str(e)}"}), 500


@app.route("/graficar", methods=["POST"])
@login_required
def graficar_legacy():
    """Endpoint legado"""
    return graficar()


@app.route("/api/derivada", methods=["POST"])
@login_required
def derivada():
    """API para calcular derivadas"""
    try:
        data = request.json or {}
        expr_text = data.get("expresion", "").strip()
        
        if not expr_text:
            return jsonify({"error": "Expresión vacía"}), 400
        
        try:
            expr = parse_expr(expr_text.replace("^", "**").replace(" ", ""),
                            transformations=standard_transformations + (implicit_multiplication_application,))
            
            resultado = diff(expr, x)
            
            return jsonify({
                "success": True,
                "input": latex(expr),
                "result": latex(resultado),
                "steps": [f"d/dx [{latex(expr)}] = {latex(resultado)}"]
            })
        
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "steps": []
            }), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/derivada", methods=["POST"])
@login_required
def derivada_legacy():
    """Endpoint legado"""
    return derivada()


# ====================================
# MANEJO DE ERRORES
# ====================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Recurso no encontrado"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Error interno del servidor"}), 500


# ====================================
# MAIN
# ====================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
