"""
CarlosTech Math AI - Motor de Integrales v5.0
Parser ultra robusto + SymPy para resolver cualquier integral
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from sympy import *
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application, convert_xor
)
import re, os, time, traceback, sqlite3, secrets, smtplib, threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import numpy as np
import json as _json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'carlostech-secret-2025')
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False,
    PERMANENT_SESSION_LIFETIME=3600
)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

SOLVER_TIMEOUT = int(os.environ.get('SOLVER_TIMEOUT', 12))

ADMIN_USER = 'admin'
ADMIN_HASH = generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123'))

DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    UNIQUE NOT NULL,
                email    TEXT    UNIQUE NOT NULL,
                password TEXT    NOT NULL,
                role     TEXT    NOT NULL DEFAULT 'student',
                created  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS password_resets (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                email   TEXT NOT NULL,
                token   TEXT UNIQUE NOT NULL,
                expiry  TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user    TEXT NOT NULL,
                tool    TEXT NOT NULL,
                input   TEXT NOT NULL,
                result  TEXT NOT NULL,
                method  TEXT NOT NULL,
                created TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key     TEXT PRIMARY KEY,
                result  TEXT NOT NULL,
                method  TEXT NOT NULL,
                steps   TEXT NOT NULL,
                hits    INTEGER NOT NULL DEFAULT 1,
                created TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS shares (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                token   TEXT UNIQUE NOT NULL,
                user    TEXT NOT NULL,
                tool    TEXT NOT NULL,
                input   TEXT NOT NULL,
                result  TEXT NOT NULL,
                method  TEXT NOT NULL,
                steps   TEXT NOT NULL,
                views   INTEGER NOT NULL DEFAULT 0,
                created TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        # Migrar columna views si no existe
        try:
            conn.execute("ALTER TABLE shares ADD COLUMN views INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        conn.commit()

init_db()

# ── Config email (variables de entorno) ──────────────────────────
MAIL_HOST = os.environ.get('MAIL_HOST', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USER = os.environ.get('MAIL_USER', '')   # tu Gmail
MAIL_PASS = os.environ.get('MAIL_PASS', '')   # contraseña de aplicación
APP_URL   = os.environ.get('APP_URL', 'http://localhost:10000')

def send_reset_email(to_email, token):
    link = f"{APP_URL}/reset/{token}"
    msg  = MIMEMultipart('alternative')
    msg['Subject'] = 'Recuperar contraseña — CarlosTech Math AI'
    msg['From']    = f'CarlosTech Math AI <{MAIL_USER}>'
    msg['To']      = to_email
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;background:#0f172a;color:#f1f5f9;border-radius:12px;padding:2rem;">
        <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:12px;padding:0.75rem 1.25rem;font-size:1.5rem;">∫</div>
            <h2 style="margin-top:1rem;letter-spacing:-0.03em;">Recuperar contraseña</h2>
        </div>
        <p style="color:#94a3b8;line-height:1.7;">Haz clic en el botón para restablecer tu contraseña. El enlace expira en <strong style="color:#f1f5f9;">30 minutos</strong>.</p>
        <div style="text-align:center;margin:2rem 0;">
            <a href="{link}" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;text-decoration:none;padding:0.875rem 2rem;border-radius:10px;font-weight:700;display:inline-block;">Restablecer contraseña</a>
        </div>
        <p style="color:#64748b;font-size:0.8rem;">Si no solicitaste esto, ignora este correo. Tu contraseña no cambiará.</p>
        <p style="color:#64748b;font-size:0.75rem;margin-top:1rem;word-break:break-all;">Enlace: {link}</p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP(MAIL_HOST, MAIL_PORT) as s:
        s.starttls()
        s.login(MAIL_USER, MAIL_PASS)
        s.sendmail(MAIL_USER, to_email, msg.as_string())

x, t, u, n = symbols('x t u n')

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)

LOCAL_DICT = {
    'x': x, 'e': E, 'E': E, 'pi': pi, 'oo': oo, 'inf': oo,
    'sin': sin, 'cos': cos, 'tan': tan, 'cot': cot, 'sec': sec, 'csc': csc,
    'asin': asin, 'acos': acos, 'atan': atan, 'arcsin': asin, 'arccos': acos, 'arctan': atan,
    'sinh': sinh, 'cosh': cosh, 'tanh': tanh, 'coth': coth,
    'asinh': asinh, 'acosh': acosh, 'atanh': atanh,
    'exp': exp, 'log': log, 'ln': log, 'sqrt': sqrt, 'Abs': Abs, 'abs': Abs,
    'sign': sign, 'floor': floor, 'ceiling': ceiling,
    'factorial': factorial, 'gamma': gamma,
}


def clean_latex(expr_str):
    """
    Convierte CUALQUIER formato de entrada a expresión SymPy válida.
    Maneja: LaTeX de MathQuill, texto plano, notación matemática estándar.
    """
    s = expr_str.strip()

    # --- 1. Eliminar prefijos de integral ---
    s = re.sub(r'\\int\s*', '', s)
    s = re.sub(r'∫\s*', '', s)
    s = re.sub(r'integral\s+(of\s+)?', '', s, flags=re.IGNORECASE)

    # --- 2. Eliminar dx, dt, du al final ---
    s = re.sub(r'\s*d[a-zA-Z]\s*$', '', s)

    # --- 3. Limpiar espacios ---
    s = s.strip()

    # --- 4. Fracciones LaTeX: \frac{a}{b} -> (a)/(b) ---
    # Primero con llaves, luego con paréntesis (después de conversión)
    for _ in range(5):  # múltiples pasadas para fracciones anidadas
        s = re.sub(r'\\frac\{([^{}]*)\}\{([^{}]*)\}', r'((\1)/(\2))', s)
    s = re.sub(r'\\frac\(([^()]*)\)\(([^()]*)\)', r'((\1)/(\2))', s)

    # --- 5. Potencias LaTeX: x^{2} -> x**(2), x^2 -> x**2 ---
    s = re.sub(r'\^\{([^}]+)\}', r'**(\1)', s)
    s = s.replace('^', '**')

    # --- 6. Llaves a paréntesis ---
    s = s.replace('{', '(').replace('}', ')')

    # --- 7. Funciones trigonométricas LaTeX ---
    trig_map = {
        r'\\operatorname\{([a-zA-Z]+)\}': r'\1',
        r'\\arcsin': 'asin', r'\\arccos': 'acos', r'\\arctan': 'atan',
        r'\\sin': 'sin', r'\\cos': 'cos', r'\\tan': 'tan',
        r'\\cot': 'cot', r'\\sec': 'sec', r'\\csc': 'csc',
        r'\\sinh': 'sinh', r'\\cosh': 'cosh', r'\\tanh': 'tanh',
        r'\\log': 'log', r'\\ln': 'log', r'\\exp': 'exp',
        r'\\sqrt': 'sqrt', r'\\abs': 'Abs',
        r'\\left': '', r'\\right': '',
        r'\\cdot': '*', r'\\times': '*',
        r'\\pi': 'pi', r'\\infty': 'oo', r'\\e': 'E',
    }
    for pattern, replacement in trig_map.items():
        s = re.sub(pattern, replacement, s)

    # --- 8. Constantes unicode ---
    s = s.replace('π', 'pi').replace('∞', 'oo').replace('∫', '')

    # --- 9. Potencias con superíndices unicode ---
    superscripts = {'⁰':'0','¹':'1','²':'2','³':'3','⁴':'4',
                    '⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9'}
    for sup, num in superscripts.items():
        s = s.replace(sup, f'**{num}')

    # --- 10. Limpiar backslashes restantes ---
    s = re.sub(r'\\([a-zA-Z]+)', r'\1', s)

    # --- 11. Número de Euler: e^x -> exp(x), e**(x) -> exp(x) ---
    s = re.sub(r'\bE\*\*\(([^)]+)\)', r'exp(\1)', s)
    s = re.sub(r'\bE\*\*([a-zA-Z0-9]+)', r'exp(\1)', s)

    # --- 12. Multiplicación implícita ---
    # 2x -> 2*x
    s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', s)
    # x2 -> x*2 (raro pero posible)
    s = re.sub(r'([a-zA-Z])(\d)', r'\1*\2', s)
    # 2( -> 2*(
    s = re.sub(r'(\d)\(', r'\1*(', s)
    # )( -> )*(
    s = re.sub(r'\)\(', r')*(', s)
    # )x -> )*x
    s = re.sub(r'\)([a-zA-Z])', r')*\1', s)
    # )2 -> )*2
    s = re.sub(r'\)(\d)', r')*\1', s)

    # --- 13. Limpiar espacios finales ---
    s = re.sub(r'\s+', '', s)

    return s


def parse_expression(expr_str):
    """Parsea una expresión con múltiples intentos de fallback."""
    cleaned = clean_latex(expr_str)
    print(f"[PARSER] Original: {repr(expr_str)}")
    print(f"[PARSER] Limpio:   {repr(cleaned)}")

    # Intento 1: parse_expr con transformaciones
    try:
        result = parse_expr(cleaned, local_dict=LOCAL_DICT, transformations=TRANSFORMATIONS)
        print(f"[PARSER] OK (intento 1): {result}")
        return result
    except Exception as e1:
        print(f"[PARSER] Intento 1 falló: {e1}")

    # Intento 2: sympify directo
    try:
        result = sympify(cleaned, locals=LOCAL_DICT)
        print(f"[PARSER] OK (intento 2): {result}")
        return result
    except Exception as e2:
        print(f"[PARSER] Intento 2 falló: {e2}")

    # Intento 3: parse_expr sin transformaciones
    try:
        result = parse_expr(cleaned, local_dict=LOCAL_DICT)
        print(f"[PARSER] OK (intento 3): {result}")
        return result
    except Exception as e3:
        print(f"[PARSER] Intento 3 falló: {e3}")

    raise ValueError(f"No se pudo parsear: '{expr_str}' -> '{cleaned}'")


def detect_method(expr, var):
    """Detecta el método de integración más apropiado."""
    try:
        # Integración por partes: polinomio * trig, polinomio * exp, polinomio * log
        args = Mul.make_args(expr)
        if len(args) >= 2:
            has_poly = any(a.is_polynomial(var) and not a.is_number for a in args)
            has_trig = any(a.has(sin, cos, tan) for a in args)
            has_exp  = any(a.has(exp) for a in args)
            has_log  = any(a.has(log) for a in args)
            if has_poly and (has_trig or has_exp or has_log):
                return "Integración por Partes"

        if expr.is_polynomial(var):
            deg = degree(expr, var)
            return f"Regla de Potencia (grado {deg})"
        if expr.is_rational_function(var) and not expr.is_polynomial(var):
            return "Fracciones Parciales"
        if expr.has(sin) or expr.has(cos) or expr.has(tan):
            if expr.has(sin) and expr.has(cos):
                return "Trigonométrica Mixta"
            return "Trigonométrica"
        if expr.has(exp):
            return "Exponencial"
        if expr.has(log):
            return "Logarítmica"
        if expr.has(sqrt):
            return "Radicales"
        if expr.has(sinh) or expr.has(cosh):
            return "Hiperbólica"
        if expr.has(asin) or expr.has(acos) or expr.has(atan):
            return "Trigonométrica Inversa"
        return "Integración Simbólica General"
    except:
        return "General"


# Mapeo de métodos a explicaciones legibles
METHOD_INFO = {
    "Regla de Potencia": {
        "icon": "📐",
        "color": "blue",
        "formula": r"\int x^n \, dx = \frac{x^{n+1}}{n+1} + C",
        "tip": "Suma 1 al exponente y divide entre el nuevo exponente."
    },
    "Trigonométrica": {
        "icon": "📡",
        "color": "purple",
        "formula": r"\int \sin(x)\,dx = -\cos(x)+C \quad \int \cos(x)\,dx = \sin(x)+C",
        "tip": "Usamos las fórmulas básicas de integración trigonométrica."
    },
    "Exponencial": {
        "icon": "📈",
        "color": "green",
        "formula": r"\int e^x \, dx = e^x + C",
        "tip": "La exponencial es su propia integral."
    },
    "Integración por Partes": {
        "icon": "🔀",
        "color": "orange",
        "formula": r"\int u \, dv = uv - \int v \, du",
        "tip": "Elegimos u y dv estratégicamente (regla LIATE)."
    },
    "Fracciones Parciales": {
        "icon": "🧩",
        "color": "pink",
        "formula": r"\frac{P(x)}{Q(x)} = \frac{A}{x-r_1} + \frac{B}{x-r_2} + \cdots",
        "tip": "Descomponemos la fracción en partes más simples."
    },
    "Radicales": {
        "icon": "🔄",
        "color": "teal",
        "formula": r"x = \sin(\theta) \text{ o } x = \tan(\theta)",
        "tip": "Usamos sustitución trigonométrica para eliminar la raíz."
    },
    "Logarítmica": {
        "icon": "📝",
        "color": "yellow",
        "formula": r"\int \ln(x) \, dx = x\ln(x) - x + C",
        "tip": "Aplicamos integración por partes con u = ln(x)."
    },
}


def generate_steps(expr, result, method, var, limits=None):
    steps = []
    v = var

    def s(title, type_, text, math=None, note=None):
        d = {"title": title, "type": type_, "text": text}
        if math: d["math"] = math
        if note: d["note"] = note
        steps.append(d)

    try:
        expr_l  = latex(expr)
        res_l   = latex(result)

        # ── PASO 1: Plantear ──────────────────────────────────────────
        if limits:
            a, b = limits
            s("Plantear la integral", "identify",
              "Tenemos una integral definida con límites de integración. "
              "El resultado será un número real (el área bajo la curva).",
              rf"\int_{{{latex(a)}}}^{{{latex(b)}}} {expr_l} \, dx")
        else:
            s("Plantear la integral", "identify",
              "Tenemos una integral indefinida. "
              "El resultado incluirá una constante de integración C, "
              "ya que la derivada de cualquier constante es cero.",
              rf"\int {expr_l} \, dx")

        # ── PASO 2: Analizar la expresión ─────────────────────────────
        simplified = simplify(expr)
        expanded   = expand(expr)
        if simplified != expr:
            s("Analizar y simplificar", "identify",
              "Antes de integrar, verificamos si la expresión puede simplificarse "
              "para facilitar el cálculo.",
              rf"{expr_l} = {latex(simplified)}")
        else:
            s("Analizar la expresión", "identify",
              "Identificamos la estructura de la función: tipo de términos, "
              "presencia de productos, cocientes o composiciones.",
              rf"f(x) = {expr_l}")

        # ── PASO 3: Método ────────────────────────────────────────────
        method_key = next((k for k in METHOD_INFO if k in method), None)
        info = METHOD_INFO.get(method_key, {"formula": "", "tip": ""})
        s(f"Método seleccionado: {method}", "method",
          info.get("tip", "Aplicamos el método más adecuado para esta expresión."),
          info.get("formula") or None)

        # ── PASO 4+: Cálculo específico por método ────────────────────

        # --- REGLA DE POTENCIA ---
        if "Potencia" in method:
            terms = Add.make_args(expanded)
            s("Separar en términos", "calc",
              f"La integral de una suma es la suma de las integrales. "
              f"Identificamos {len(terms)} término(s) independiente(s):",
              rf"{latex(expanded)}")
            partial_results = []
            running = S.Zero
            for term in terms:
                coeff, base = term.as_coeff_Mul()
                int_term = integrate(term, v)
                running += int_term
                # Explicar la regla aplicada
                if base.is_symbol:          # coeff·x^1
                    rule = rf"\int {latex(term)}\,dx = \frac{{{latex(coeff)}x^2}}{{2}}"
                elif base.is_Number:        # constante
                    rule = rf"\int {latex(term)}\,dx = {latex(term)} \cdot x"
                else:
                    p = base.as_base_exp()[1] if base.is_Pow else 1
                    rule = rf"\int {latex(term)}\,dx = {latex(int_term)}"
                partial_results.append(rule)
            s("Aplicar la Regla de Potencia a cada término", "calc",
              r"Regla: $\int x^n\,dx = \dfrac{x^{n+1}}{n+1}$ — sumamos 1 al exponente y dividimos entre el nuevo exponente.",
              r"\\[6pt]".join(partial_results))
            s("Combinar los resultados", "calc",
              "Sumamos todas las antiderivadas parciales obtenidas:",
              rf"F(x) = {latex(integrate(expanded, v))}")

        # --- TRIGONOMÉTRICA SIMPLE ---
        elif "Trigonométrica" in method and "Mixta" not in method and "Partes" not in method:
            if expr.has(sin) and not expr.has(cos):
                s("Reconocer la fórmula del seno", "calc",
                  "Esta es una integral trigonométrica directa. "
                  "La antiderivada del seno es el coseno negativo:",
                  rf"\int \sin(ax)\,dx = -\frac{{1}}{{a}}\cos(ax) + C")
                s("Aplicar la fórmula", "calc",
                  "Sustituimos directamente en la fórmula:",
                  rf"\int {expr_l}\,dx = {res_l}")
            elif expr.has(cos) and not expr.has(sin):
                s("Reconocer la fórmula del coseno", "calc",
                  "La antiderivada del coseno es el seno:",
                  rf"\int \cos(ax)\,dx = \frac{{1}}{{a}}\sin(ax) + C")
                s("Aplicar la fórmula", "calc",
                  "Sustituimos directamente:",
                  rf"\int {expr_l}\,dx = {res_l}")
            elif expr.has(tan):
                s("Reescribir la tangente", "calc",
                  "Expresamos tan(x) como cociente para poder integrar:",
                  rf"\tan(x) = \frac{{\sin(x)}}{{\cos(x)}}")
                s("Aplicar sustitución u = cos(x)", "calc",
                  "Con u = cos(x), du = −sin(x)dx, la integral se convierte en −∫du/u:",
                  rf"\int \tan(x)\,dx = -\ln|\cos(x)| + C")
            else:
                s("Aplicar fórmula trigonométrica", "calc",
                  "Usamos la tabla de integrales trigonométricas estándar:",
                  rf"\int {expr_l}\,dx = {res_l}")

        # --- TRIGONOMÉTRICA MIXTA ---
        elif "Mixta" in method:
            s("Aplicar identidad de producto", "calc",
              "Cuando aparece sin(x)·cos(x), usamos la identidad del ángulo doble "
              "para reducir el grado de la expresión:",
              rf"\sin(x)\cos(x) = \frac{{\sin(2x)}}{{2}}")
            s("Integrar la expresión reducida", "calc",
              "Ahora la integral es directa con la fórmula del seno:",
              rf"\int \frac{{\sin(2x)}}{{2}}\,dx = -\frac{{\cos(2x)}}{{4}} + C")

        # --- EXPONENCIAL ---
        elif "Exponencial" in method and "Partes" not in method:
            coeff_info = ""
            try:
                # Detectar e^(ax)
                arg = expr.rewrite(exp).find(exp)
                if arg:
                    inner = list(arg)[0].args[0]
                    c = inner.coeff(v)
                    if c and c != 1:
                        coeff_info = f" El coeficiente interno es {latex(c)}, así que dividimos entre él."
            except: pass
            s("Propiedad fundamental de la exponencial", "calc",
              "La función exponencial es su propia antiderivada. "
              "Si hay un coeficiente en el exponente, dividimos entre él." + coeff_info,
              rf"\int e^{{ax}}\,dx = \frac{{1}}{{a}}e^{{ax}} + C")
            s("Aplicar la fórmula", "calc",
              "Sustituimos los valores concretos:",
              rf"\int {expr_l}\,dx = {res_l}")

        # --- INTEGRACIÓN POR PARTES ---
        elif "Partes" in method:
            s("Regla LIATE para elegir u", "calc",
              "La regla LIATE nos dice el orden de prioridad para elegir u: "
              "Logarítmica → Inversa trig. → Algebraica → Trigonométrica → Exponencial. "
              "Elegimos u como el factor de mayor prioridad.",
              rf"\int u\,dv = uv - \int v\,du")
            args = Mul.make_args(expr)
            u_c = dv_c = None
            for arg in args:
                if arg.has(log) or (arg.is_polynomial(v) and not arg.is_number):
                    u_c = arg
                else:
                    dv_c = arg
            if u_c is None: u_c = args[0]
            if dv_c is None: dv_c = Mul(*[a for a in args if a is not u_c])
            try:
                du_c = diff(u_c, v)
                vi_c = integrate(dv_c, v)
                s("Asignar u y dv", "calc",
                  f"Elegimos u = {latex(u_c)} porque tiene mayor prioridad LIATE. "
                  f"El resto es dv:",
                  rf"u = {latex(u_c)} \qquad dv = {latex(dv_c)}\,dx")
                s("Calcular du y v", "calc",
                  "Derivamos u para obtener du, e integramos dv para obtener v:",
                  rf"du = {latex(du_c)}\,dx \qquad v = {latex(vi_c)}")
                remaining = integrate(vi_c * du_c, v)
                s("Sustituir en la fórmula", "calc",
                  "Aplicamos ∫u dv = uv − ∫v du y resolvemos la integral restante:",
                  rf"\int {expr_l}\,dx = {latex(u_c)}\cdot{latex(vi_c)} - \int {latex(vi_c)}\cdot{latex(du_c)}\,dx")
                s("Resolver la integral restante", "calc",
                  "La integral que queda es más simple y la resolvemos directamente:",
                  rf"\int {latex(vi_c * du_c)}\,dx = {latex(remaining)}")
            except: pass

        # --- FRACCIONES PARCIALES ---
        elif "Fracciones" in method:
            apart_expr = apart(expr, v)
            numer, denom = fraction(expr)
            s("Factorizar el denominador", "calc",
              "Para descomponer en fracciones parciales, primero factorizamos el denominador "
              "e identificamos sus raíces:",
              rf"\text{{Denominador: }} {latex(denom)}")
            s("Descomponer en fracciones simples", "calc",
              "Reescribimos la fracción como suma de fracciones con denominadores simples. "
              "Cada factor lineal genera un término A/(x−r):",
              rf"{latex(expr)} = {latex(apart_expr)}")
            s("Integrar cada fracción", "calc",
              "Cada fracción simple se integra con la fórmula ∫1/(x−a)dx = ln|x−a|:",
              rf"\int {latex(apart_expr)}\,dx = {res_l}")

        # --- LOGARÍTMICA ---
        elif "Logarítmica" in method:
            if expr == log(v):
                s("Reconocer integral de ln(x)", "calc",
                  "Esta integral no es directa. Usamos integración por partes con u = ln(x), dv = dx:",
                  rf"u = \ln(x),\quad dv = dx \implies du = \frac{{1}}{{x}}dx,\quad v = x")
                s("Aplicar integración por partes", "calc",
                  "Sustituimos en la fórmula ∫u dv = uv − ∫v du:",
                  rf"\int \ln(x)\,dx = x\ln(x) - \int x \cdot \frac{{1}}{{x}}\,dx = x\ln(x) - x + C")
            else:
                s("Aplicar fórmula logarítmica", "calc",
                  "Usamos la regla ∫1/x dx = ln|x| o integramos por partes según el caso:",
                  rf"\int {expr_l}\,dx = {res_l}")

        # --- RADICALES ---
        elif "Radicales" in method:
            s("Identificar la sustitución", "calc",
              "Las raíces cuadradas se eliminan con sustitución trigonométrica. "
              "Según la forma del radicando elegimos la sustitución adecuada:",
              rf"\sqrt{{1-x^2}} \to x=\sin\theta \quad \sqrt{{1+x^2}} \to x=\tan\theta \quad \sqrt{{x^2-1}} \to x=\sec\theta")
            s("Aplicar la sustitución", "calc",
              "Sustituimos, simplificamos usando identidades pitagóricas y resolvemos:",
              rf"\int {expr_l}\,dx = {res_l}")

        # --- HIPERBÓLICA ---
        elif "Hiperbólica" in method:
            s("Fórmulas hiperbólicas", "calc",
              "Las funciones hiperbólicas tienen antiderivadas análogas a las trigonométricas:",
              rf"\int \sinh(x)\,dx = \cosh(x)+C \qquad \int \cosh(x)\,dx = \sinh(x)+C")
            s("Aplicar la fórmula", "calc",
              "Sustituimos directamente:",
              rf"\int {expr_l}\,dx = {res_l}")

        # --- TRIG INVERSA ---
        elif "Inversa" in method:
            s("Fórmulas de trigonométricas inversas", "calc",
              "Reconocemos la forma estándar que genera arcoseno, arcocoseno o arcotangente:",
              rf"\int \frac{{1}}{{\sqrt{{1-x^2}}}}\,dx = \arcsin(x)+C \qquad \int \frac{{1}}{{1+x^2}}\,dx = \arctan(x)+C")
            s("Aplicar la fórmula", "calc",
              "Identificamos la forma y sustituimos:",
              rf"\int {expr_l}\,dx = {res_l}")

        # --- GENERAL ---
        else:
            s("Aplicar integración simbólica", "calc",
              "Usamos el motor simbólico con múltiples estrategias (expansión, simplificación, "
              "reescritura) para encontrar la antiderivada:",
              rf"\int {expr_l}\,dx = {res_l}")

        # ── PASO: Verificación ────────────────────────────────────────
        if not limits:
            try:
                deriv = diff(result, v)
                deriv_s = simplify(deriv)
                expr_s  = simplify(expr)
                match = simplify(deriv_s - expr_s) == 0
                s("Verificar derivando el resultado", "verify",
                  "Una forma de comprobar que la integral es correcta es derivar el resultado "
                  "y verificar que obtenemos la función original:",
                  rf"\frac{{d}}{{dx}}\left[{res_l}\right] = {latex(deriv_s)}",
                  note="✓ Verificado" if match else "⚠ Revisar simplificación")
            except: pass

        # ── PASO FINAL ────────────────────────────────────────────────
        if limits:
            a, b = limits
            antideriv = integrate(expr, v)
            fa = antideriv.subs(v, b)
            fb = antideriv.subs(v, a)
            s("Evaluar en los límites (Teorema Fundamental)", "result",
              f"Aplicamos el Teorema Fundamental del Cálculo: F(b) − F(a). "
              f"Sustituimos x = {latex(b)} y x = {latex(a)} en la antiderivada:",
              rf"\Big[{latex(antideriv)}\Big]_{{{latex(a)}}}^{{{latex(b)}}} "
              rf"= \left({latex(fa)}\right) - \left({latex(fb)}\right) = {res_l}")
        else:
            s("Resultado final", "result",
              "La antiderivada completa es (recuerda que C representa cualquier constante real, "
              "ya que su derivada es siempre cero):",
              rf"\boxed{{\int {expr_l}\,dx = {res_l} + C}}")

    except Exception:
        steps = [
            {"title": "Expresión",  "type": "identify", "text": "Integral a resolver:",  "math": latex(expr)},
            {"title": "Resultado",  "type": "result",   "text": "Resultado obtenido:",   "math": latex(result) + ("" if limits else " + C")},
        ]

    return steps


class IntegralSolver:
    def __init__(self, expr_str, var='x', limits=None):
        self.expr_str = expr_str
        self.var = Symbol(var)
        self.limits = limits
        self.expr = None
        self.result = None
        self.method = None
        self.steps = []
        self.errors = []
        self.t0 = time.time()

    def solve(self):
        # 1. Parsear
        try:
            self.expr = parse_expression(self.expr_str)
        except Exception as e:
            self.errors.append(f"Error al parsear: {str(e)}")
            return False

        # 2. Detectar método
        self.method = detect_method(self.expr, self.var)

        # 3. Resolver con múltiples estrategias
        result = self._try_all_strategies()

        if result is None:
            self.errors.append("No se encontró solución analítica para esta integral.")
            return False

        self.result = result

        # 4. Generar pasos
        self.steps = generate_steps(
            self.expr, self.result, self.method, self.var, self.limits
        )
        return True

    def _try_all_strategies(self):
        """Intenta todas las estrategias disponibles en orden."""
        expr = self.expr
        var = self.var

        # Estrategia 1: Integración directa SymPy
        result = self._try(lambda: (
            integrate(expr, (var, self.limits[0], self.limits[1]))
            if self.limits else
            integrate(expr, var)
        ))
        if result is not None:
            print(f"[SOLVER] Estrategia 1 OK: {result}")
            return result

        # Estrategia 2: Expandir y reintentar
        result = self._try(lambda: (
            integrate(expand(expr), (var, self.limits[0], self.limits[1]))
            if self.limits else
            integrate(expand(expr), var)
        ))
        if result is not None:
            print(f"[SOLVER] Estrategia 2 OK: {result}")
            return result

        # Estrategia 3: Simplificar y reintentar
        result = self._try(lambda: (
            integrate(simplify(expr), (var, self.limits[0], self.limits[1]))
            if self.limits else
            integrate(simplify(expr), var)
        ))
        if result is not None:
            print(f"[SOLVER] Estrategia 3 OK: {result}")
            return result

        # Estrategia 4: Trigsimp para trigonométricas
        if expr.has(sin) or expr.has(cos) or expr.has(tan):
            result = self._try(lambda: (
                integrate(trigsimp(expr), (var, self.limits[0], self.limits[1]))
                if self.limits else
                integrate(trigsimp(expr), var)
            ))
            if result is not None:
                print(f"[SOLVER] Estrategia 4 (trigsimp) OK: {result}")
                return result

        # Estrategia 5: Apart para racionales
        result = self._try(lambda: (
            integrate(apart(expr, var), (var, self.limits[0], self.limits[1]))
            if self.limits else
            integrate(apart(expr, var), var)
        ))
        if result is not None:
            print(f"[SOLVER] Estrategia 5 (apart) OK: {result}")
            return result

        # Estrategia 6: Rewrite en formas alternativas
        for rewrite_form in [exp, cos, sin, tan, log]:
            result = self._try(lambda f=rewrite_form: (
                integrate(expr.rewrite(f), (var, self.limits[0], self.limits[1]))
                if self.limits else
                integrate(expr.rewrite(f), var)
            ))
            if result is not None:
                print(f"[SOLVER] Estrategia 6 (rewrite {rewrite_form}) OK: {result}")
                return result

        # Estrategia 7: meijerg=True para funciones especiales
        if not self.limits:
            result = self._try(lambda: integrate(expr, var, meijerg=True))
            if result is not None and not result.has(Integral):
                print(f"[SOLVER] Estrategia 7 (meijerg) OK: {result}")
                return result

        # Estrategia 8: manual_integral para casos difíciles
        if not self.limits:
            result = self._try(lambda: integrate(expr, var, manual=True))
            if result is not None and not result.has(Integral):
                print(f"[SOLVER] Estrategia 8 (manual) OK: {result}")
                return result

        print("[SOLVER] Todas las estrategias fallaron")
        return None

    def _try(self, fn):
        """Ejecuta una función y retorna None si falla o si el resultado es inválido."""
        try:
            r = fn()
            if r is None:
                return None
            if r == oo or r == -oo or r == zoo or r == nan:
                return None
            if isinstance(r, Integral):
                return None
            # Verificar que no sea una integral sin resolver
            if hasattr(r, 'has') and r.has(Integral):
                return None
            return r
        except Exception as e:
            print(f"[SOLVER] Estrategia falló: {e}")
            return None

    def get_response(self):
        success = self.result is not None
        return {
            "success": success,
            "input": latex(self.expr) if self.expr else self.expr_str,
            "result": latex(self.result) if self.result else "No se pudo resolver",
            "method_detected": self.method or "Desconocido",
            "steps": self.steps,
            "errors": self.errors,
            "computation_time": f"{time.time() - self.t0:.3f}s"
        }


# ============ AUTH ============

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"error": "No autenticado"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def landing():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template("landing.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == ADMIN_USER and check_password_hash(ADMIN_HASH, password):
            session['user']  = ADMIN_USER
            session['email'] = 'admin@carlostech.ai'
            session['role']  = 'admin'
            return redirect(url_for('dashboard'))
        with get_db() as conn:
            row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if row and check_password_hash(row['password'], password):
            session['user']  = row['username']
            session['email'] = row['email']
            session['role']  = row['role']
            session['uid']   = row['id']
            return redirect(url_for('dashboard'))
        return render_template("login.html", error="Usuario o contraseña incorrectos")
    return render_template("login.html")


@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        with get_db() as conn:
            row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if row:
            token  = secrets.token_urlsafe(32)
            expiry = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
            with get_db() as conn:
                conn.execute("DELETE FROM password_resets WHERE email=?", (email,))
                conn.execute("INSERT INTO password_resets (email, token, expiry) VALUES (?,?,?)", (email, token, expiry))
                conn.commit()
            try:
                send_reset_email(email, token)
            except Exception as e:
                print(f"[MAIL] Error: {e}")
                return render_template("forgot.html", error="No se pudo enviar el correo. Verifica la configuración SMTP.")
        # Siempre mostrar éxito (no revelar si el email existe)
        return render_template("forgot.html", sent=True)
    return render_template("forgot.html")


@app.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    if 'user' in session:
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        row = conn.execute("SELECT * FROM password_resets WHERE token=?", (token,)).fetchone()
    if not row or datetime.utcnow() > datetime.fromisoformat(row['expiry']):
        return render_template("reset.html", invalid=True)
    if request.method == "POST":
        password = request.form.get("password", "").strip()
        confirm  = request.form.get("confirm",  "").strip()
        if len(password) < 6:
            return render_template("reset.html", error="La contraseña debe tener al menos 6 caracteres")
        if password != confirm:
            return render_template("reset.html", error="Las contraseñas no coinciden")
        with get_db() as conn:
            conn.execute("UPDATE users SET password=? WHERE email=?", (generate_password_hash(password), row['email']))
            conn.execute("DELETE FROM password_resets WHERE token=?", (token,))
            conn.commit()
        return redirect(url_for('login') + '?reset=1')
    return render_template("reset.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email",    "").strip().lower()
        password = request.form.get("password", "").strip()
        confirm  = request.form.get("confirm",  "").strip()
        if not username or not email or not password:
            return render_template("register.html", error="Todos los campos son obligatorios")
        if len(username) < 3:
            return render_template("register.html", error="El usuario debe tener al menos 3 caracteres")
        if len(password) < 6:
            return render_template("register.html", error="La contraseña debe tener al menos 6 caracteres")
        if password != confirm:
            return render_template("register.html", error="Las contraseñas no coinciden")
        if '@' not in email:
            return render_template("register.html", error="Email inválido")
        if username == ADMIN_USER:
            return render_template("register.html", error="Ese nombre de usuario no está disponible")
        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (username, email, password) VALUES (?,?,?)",
                    (username, email, generate_password_hash(password))
                )
                conn.commit()
            return redirect(url_for('login') + '?registered=1')
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                return render_template("register.html", error="Ese nombre de usuario ya existe")
            if 'email' in str(e):
                return render_template("register.html", error="Ese email ya está registrado")
            return render_template("register.html", error="Error al registrar")
    return render_template("register.html")


@app.route("/app")
@login_required
def dashboard():
    return render_template("index.html",
        username=session.get('user', 'admin'),
        email=session.get('email', 'admin@carlostech.ai'),
        role=session.get('role', 'admin')
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            return jsonify({"error": "Acceso denegado"}), 403
        return f(*args, **kwargs)
    return decorated


@app.route("/admin")
@login_required
def admin_panel():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        users = conn.execute("SELECT id,username,email,role,created FROM users ORDER BY created DESC").fetchall()
        total_calcs = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        total_shares = conn.execute("SELECT COUNT(*) FROM shares").fetchone()[0]
        recent = conn.execute(
            "SELECT user,tool,input,result,created FROM history ORDER BY created DESC LIMIT 20"
        ).fetchall()
    return render_template("admin.html",
        users=users, total_calcs=total_calcs,
        total_shares=total_shares, recent=recent,
        username=session['user'], email=session.get('email',''), role='admin'
    )


@app.route("/api/admin/delete-user/<int:uid>", methods=["DELETE"])
@login_required
@admin_required
def admin_delete_user(uid):
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id=?", (uid,))
        conn.execute("DELETE FROM history WHERE user=(SELECT username FROM users WHERE id=?)", (uid,))
        conn.commit()
    return jsonify({"ok": True})


@app.route("/api/history", methods=["GET"])
@login_required
def api_history_get():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT tool,input,result,method,created FROM history WHERE user=? ORDER BY created DESC LIMIT 50",
            (session['user'],)
        ).fetchall()
    # Enriquecer con vistas de shares del mismo usuario
    result_list = [dict(r) for r in rows]
    with get_db() as conn:
        shares_views = conn.execute(
            "SELECT input, SUM(views) as total_views FROM shares WHERE user=? GROUP BY input",
            (session['user'],)
        ).fetchall()
    views_map = {r['input']: r['total_views'] for r in shares_views}
    for item in result_list:
        item['views'] = views_map.get(item['input'], 0)
    return jsonify(result_list)


@app.route("/api/history", methods=["POST"])
@login_required
def api_history_save():
    data = request.json or {}
    with get_db() as conn:
        conn.execute(
            "INSERT INTO history (user,tool,input,result,method) VALUES (?,?,?,?,?)",
            (session['user'], data.get('tool',''), data.get('input',''),
             data.get('result',''), data.get('method',''))
        )
        conn.commit()
    return jsonify({"ok": True})


@app.route("/api/history", methods=["DELETE"])
@login_required
def api_history_clear():
    with get_db() as conn:
        conn.execute("DELETE FROM history WHERE user=?", (session['user'],))
        conn.commit()
    return jsonify({"ok": True})


@app.route("/api/cambiar-password", methods=["POST"])
@login_required
def api_cambiar_password():
    if session.get('role') == 'admin' and session.get('user') == ADMIN_USER:
        return jsonify({"error": "El admin usa variables de entorno para cambiar su contraseña"}), 400
    data = request.json or {}
    actual  = data.get('actual', '').strip()
    nueva   = data.get('nueva', '').strip()
    confirm = data.get('confirm', '').strip()
    if not actual or not nueva:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400
    if len(nueva) < 6:
        return jsonify({"error": "La nueva contraseña debe tener al menos 6 caracteres"}), 400
    if nueva != confirm:
        return jsonify({"error": "Las contraseñas no coinciden"}), 400
    with get_db() as conn:
        row = conn.execute("SELECT password FROM users WHERE username=?", (session['user'],)).fetchone()
    if not row or not check_password_hash(row['password'], actual):
        return jsonify({"error": "Contraseña actual incorrecta"}), 400
    with get_db() as conn:
        conn.execute("UPDATE users SET password=? WHERE username=?",
                     (generate_password_hash(nueva), session['user']))
        conn.commit()
    return jsonify({"ok": True})


# ── Helpers de caché ────────────────────────────────────────────

def cache_key(expr_text, a, b):
    return f"{expr_text.strip()}|{a}|{b}"

def cache_get(key):
    with get_db() as conn:
        row = conn.execute("SELECT result, method, steps FROM cache WHERE key=?", (key,)).fetchone()
        if row:
            conn.execute("UPDATE cache SET hits = hits + 1 WHERE key=?", (key,))
            conn.commit()
    return dict(row) if row else None

def cache_set(key, result, method, steps):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cache (key, result, method, steps) VALUES (?,?,?,?)",
            (key, result, method, _json.dumps(steps))
        )
        conn.commit()

# ── Solver con timeout ───────────────────────────────────────────

def solve_with_timeout(expr_text, limits, timeout=SOLVER_TIMEOUT):
    result_container = {}

    def target():
        try:
            solver = IntegralSolver(expr_text, limits=limits)
            solver.solve()
            result_container['resp'] = solver.get_response()
        except Exception as e:
            result_container['resp'] = {
                "success": False,
                "error": str(e),
                "steps": [],
                "input": expr_text,
                "result": "",
                "method_detected": "",
                "computation_time": f"{timeout}s"
            }

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)

    if t.is_alive():
        return {
            "success": False,
            "error": f"El cálculo tardó más de {timeout}s. Intenta simplificar la expresión.",
            "steps": [],
            "input": expr_text,
            "result": "",
            "method_detected": "Timeout",
            "computation_time": f"{timeout}s"
        }
    return result_container.get('resp', {"success": False, "error": "Error desconocido", "steps": []})


@app.route("/api/simplificar", methods=["POST"])
@login_required
@limiter.limit("30 per minute; 5 per second")
def api_simplificar():
    try:
        data = request.json or {}
        expr_text = data.get("expresion", "").strip()
        op        = data.get("operacion", "simplify")
        if not expr_text:
            return jsonify({"error": "Expresion vacia"}), 400
        expr = parse_expression(expr_text)
        ops  = {
            "simplify":  lambda e: simplify(e),
            "expand":    lambda e: expand(e),
            "factor":    lambda e: factor(e),
            "cancel":    lambda e: cancel(e),
            "apart":     lambda e: apart(e, x),
            "trigsimp":  lambda e: trigsimp(e),
        }
        fn = ops.get(op, ops["simplify"])
        result = fn(expr)
        el, rl = latex(expr), latex(result)
        steps = [
            {"title": "Expresión original", "type": "identify", "text": "Expresión a procesar:", "math": el},
            {"title": f"Aplicar {op}",       "type": "calc",     "text": f"Aplicamos la operación '{op}' sobre la expresión:", "math": rf"{el} \\longrightarrow {rl}"},
            {"title": "Resultado",           "type": "result",   "text": "Resultado final:", "math": rf"\\boxed{{{rl}}}"},
        ]
        return jsonify({"success": True, "input": el, "result": rl, "steps": steps})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "steps": []}), 400


@app.route("/api/resolver", methods=["POST"])
@login_required
@limiter.limit("30 per minute; 5 per second")
def api_resolver():
    try:
        data = request.json or {}
        expr_text = data.get("integral", "").strip()
        a = data.get("a")
        b = data.get("b")

        if not expr_text:
            return jsonify({"success": False, "error": "Expresión vacía", "steps": []}), 400

        limits = None
        if a not in (None, "") and b not in (None, ""):
            try:
                limits = (sympify(str(a)), sympify(str(b)))
            except:
                pass

        # Buscar en caché
        ck = cache_key(expr_text, a, b)
        cached = cache_get(ck)
        if cached:
            print(f"[CACHE] Hit: {ck}")
            return jsonify({
                "success": True,
                "input": expr_text,
                "result": cached['result'],
                "method_detected": cached['method'] + " (caché)",
                "steps": _json.loads(cached['steps']),
                "computation_time": "0.001s",
                "cached": True
            })

        resp = solve_with_timeout(expr_text, limits)

        # Guardar en caché si fue exitoso
        if resp.get('success'):
            cache_set(ck, resp['result'], resp['method_detected'], resp['steps'])

        return jsonify(resp), 200 if resp["success"] else 400

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "steps": []}), 500


@app.route("/api/graficar", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def api_graficar():
    try:
        data = request.json or {}
        expr_text = data.get("integral", "").strip()
        if not expr_text:
            return jsonify({"error": "Expresión vacía"}), 400

        try:
            expr = parse_expression(expr_text)
        except Exception as e:
            return jsonify({"error": f"Error al parsear: {e}"}), 400

        a = data.get("a")
        b = data.get("b")
        try:
            a_val = float(a) if a not in (None, "") else -5.0
            b_val = float(b) if b not in (None, "") else 5.0
        except:
            a_val, b_val = -5.0, 5.0

        x_vals = np.linspace(a_val, b_val, 500)
        y_list = []

        try:
            f = lambdify(x, expr, modules=['numpy'])
            y_raw = f(x_vals)
            for yv in (y_raw if hasattr(y_raw, '__iter__') else [y_raw] * len(x_vals)):
                try:
                    yf = float(yv)
                    y_list.append(None if (np.isnan(yf) or np.isinf(yf)) else yf)
                except:
                    y_list.append(None)
        except:
            for xv in x_vals:
                try:
                    yf = float(expr.subs(x, xv))
                    y_list.append(None if (np.isnan(yf) or np.isinf(yf)) else yf)
                except:
                    y_list.append(None)

        return jsonify({"x": x_vals.tolist(), "y": y_list, "a": a_val, "b": b_val})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/derivada", methods=["POST"])
@login_required
@limiter.limit("30 per minute; 5 per second")
def api_derivada():
    try:
        data = request.json or {}
        expr_text = data.get("expresion", "").strip()
        orden = int(data.get("orden", 1))
        if not expr_text:
            return jsonify({"error": "Expresion vacia"}), 400
        expr   = parse_expression(expr_text)
        result = diff(expr, x, orden)
        steps  = _deriv_steps(expr, result, orden)
        return jsonify({"success": True, "input": latex(expr), "result": latex(result), "steps": steps})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "steps": []}), 400


@app.route("/api/limite", methods=["POST"])
@login_required
@limiter.limit("30 per minute; 5 per second")
def api_limite():
    try:
        data = request.json or {}
        expr_text = data.get("expresion", "").strip()
        punto_str = data.get("punto", "0")
        direccion = data.get("direccion", "+-")
        if not expr_text:
            return jsonify({"error": "Expresion vacia"}), 400
        expr    = parse_expression(expr_text)
        punto_s = sympify(str(punto_str), locals=LOCAL_DICT)
        result  = limit(expr, x, punto_s, direccion)
        steps   = _limit_steps(expr, result, punto_s, direccion)
        return jsonify({"success": True, "input": latex(expr), "punto": latex(punto_s),
                        "result": latex(result), "steps": steps})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "steps": []}), 400


@app.route("/api/taylor", methods=["POST"])
@login_required
@limiter.limit("30 per minute; 5 per second")
def api_taylor():
    try:
        data = request.json or {}
        expr_text = data.get("expresion", "").strip()
        punto_str = data.get("punto", "0")
        orden     = int(data.get("orden", 6))
        if not expr_text:
            return jsonify({"error": "Expresion vacia"}), 400
        expr    = parse_expression(expr_text)
        punto_s = sympify(str(punto_str), locals=LOCAL_DICT)
        serie   = series(expr, x, punto_s, orden)
        polinomio = serie.removeO()
        steps   = _taylor_steps(expr, serie, polinomio, punto_s, orden)
        return jsonify({"success": True, "input": latex(expr), "punto": latex(punto_s),
                        "orden": orden, "result": latex(polinomio), "serie": latex(serie), "steps": steps})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "steps": []}), 400


@app.route("/api/ode", methods=["POST"])
@login_required
@limiter.limit("20 per minute; 3 per second")
def api_ode():
    try:
        data = request.json or {}
        expr_text = data.get("expresion", "").strip()
        if not expr_text:
            return jsonify({"error": "Expresion vacia"}), 400
        y_fn = Function('y')
        expr_clean = clean_latex(expr_text)
        expr_clean = re.sub(r"y''", "Derivative(y(x),x,2)", expr_clean)
        expr_clean = re.sub(r"y'",  "Derivative(y(x),x)",   expr_clean)
        expr_clean = re.sub(r"\by\b", "y(x)", expr_clean)
        ode_local  = {**LOCAL_DICT, 'y': y_fn, 'Derivative': Derivative}
        ode_expr   = sympify(expr_clean, locals=ode_local)
        if not isinstance(ode_expr, Eq):
            ode_expr = Eq(ode_expr, 0)
        sol   = dsolve(ode_expr, y_fn(x))
        steps = _ode_steps(ode_expr, sol)
        return jsonify({"success": True, "input": latex(ode_expr), "result": latex(sol), "steps": steps})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "steps": []}), 400


# ── Generadores de pasos ─────────────────────────────────────────

def _step(title, type_, text, math=None):
    d = {"title": title, "type": type_, "text": text}
    if math:
        d["math"] = math
    return d


def _deriv_steps(expr, result, orden):
    el = latex(expr)
    rl = latex(result)
    ord_str = {1: "primera", 2: "segunda", 3: "tercera"}.get(orden, f"orden {orden}")
    lhs = (rf"\frac{{d^{{{orden}}}}}{{dx^{{{orden}}}}}\left[{el}\right]"
           if orden > 1 else rf"\frac{{d}}{{dx}}\left[{el}\right]")
    steps = [
        _step("Plantear la derivada", "identify",
              f"Calculamos la derivada de {ord_str} orden:", lhs)
    ]
    if expr.is_polynomial(x):
        terms = Add.make_args(expand(expr))
        partials = [rf"\frac{{d}}{{dx}}[{latex(t)}]={latex(diff(t,x))}" for t in terms]
        steps += [
            _step("Regla de la potencia", "method",
                  "Para cada termino xn: d/dx[xn] = n*x^(n-1)",
                  rf"\frac{{d}}{{dx}}[x^n]=n\cdot x^{{n-1}}"),
            _step("Derivar termino a termino", "calc",
                  "La derivada de una suma es la suma de las derivadas:",
                  r"\qquad".join(partials)),
        ]
    elif expr.has(sin) or expr.has(cos):
        steps.append(_step("Reglas trigonometricas", "method",
                           "Aplicamos las reglas de derivacion trigonometrica:",
                           rf"\frac{{d}}{{dx}}[\sin x]=\cos x\qquad\frac{{d}}{{dx}}[\cos x]=-\sin x"))
    elif expr.has(exp):
        steps.append(_step("Regla exponencial", "method",
                           "La exponencial es su propia derivada:",
                           rf"\frac{{d}}{{dx}}[e^{{ax}}]=a\cdot e^{{ax}}"))
    elif expr.has(log):
        steps.append(_step("Regla logaritmo", "method",
                           "Derivada del logaritmo natural:",
                           rf"\frac{{d}}{{dx}}[\ln x]=\frac{{1}}{{x}}"))
    steps.append(_step("Resultado", "result",
                       f"La derivada de {ord_str} orden es:",
                       rf"\boxed{{{lhs}={rl}}}"))
    return steps


def _limit_steps(expr, result, punto, direccion):
    el  = latex(expr)
    rl  = latex(result)
    pl  = latex(punto)
    sup = {"+": "^+", "-": "^-", "+-": ""}.get(str(direccion), "")
    steps = [
        _step("Plantear el limite", "identify",
              f"Calculamos el limite cuando x tiende a {pl}:",
              rf"\lim_{{x\to {pl}{sup}}}{el}")
    ]
    try:
        direct = simplify(expr.subs(x, punto))
        if direct.is_finite and direct not in (zoo, nan):
            steps.append(_step("Sustitucion directa", "calc",
                               f"Sustituimos x = {pl} directamente:",
                               rf"{el}\Big|_{{x={pl}}}={latex(direct)}"))
        else:
            steps.append(_step("Forma indeterminada", "calc",
                               "La sustitucion directa da una forma indeterminada:",
                               rf"{el}\Big|_{{x={pl}}}={latex(direct)}"))
            num, den = fraction(expr)
            if den != 1:
                steps.append(_step("Regla de L'Hopital", "method",
                                   "Derivamos numerador y denominador por separado:",
                                   rf"\lim_{{x\to{pl}}}\frac{{{latex(num)}}}{{{latex(den)}}}="
                                   rf"\lim_{{x\to{pl}}}\frac{{{latex(diff(num,x))}}}{{{latex(diff(den,x))}}}"))
    except Exception:
        pass
    steps.append(_step("Resultado", "result", "El valor del limite es:",
                       rf"\boxed{{\lim_{{x\to {pl}{sup}}}{el}={rl}}}"))
    return steps


def _taylor_steps(expr, serie, polinomio, punto, orden):
    el = latex(expr)
    pl = latex(punto)
    steps = [
        _step("Plantear la serie", "identify",
              f"Expandimos f(x) en serie de Taylor alrededor de x={pl} hasta orden {orden}:",
              rf"f(x)=\sum_{{n=0}}^{{\infty}}\frac{{f^{{(n)}}({pl})}}{{n!}}(x-{pl})^n"),
        _step("Formula de coeficientes", "method",
              "Cada coeficiente se obtiene evaluando la n-esima derivada en el punto:",
              rf"a_n=\frac{{f^{{(n)}}({pl})}}{{n!}}"),
    ]
    deriv_vals = []
    f_val = expr
    for n in range(min(5, orden)):
        val = simplify(f_val.subs(x, punto))
        deriv_vals.append(rf"f^{{({n})}}({pl})={latex(val)}")
        f_val = diff(f_val, x)
    steps += [
        _step("Derivadas en el punto", "calc",
              "Evaluamos las primeras derivadas en el punto de expansion:",
              r"\qquad".join(deriv_vals)),
        _step("Polinomio de Taylor", "calc",
              f"El polinomio de Taylor de grado {orden-1} es:",
              latex(polinomio)),
        _step("Serie con termino de error", "result",
              "La serie completa con el termino O(x^n) es:",
              rf"\boxed{{{latex(serie)}}}"),
    ]
    return steps


def _ode_steps(ode_expr, sol):
    steps = [
        _step("Plantear la ODE", "identify",
              "Tenemos la siguiente ecuacion diferencial ordinaria:",
              latex(ode_expr))
    ]
    hint = "general"
    try:
        hint = classify_ode(ode_expr, Function('y')(x))[0]
    except Exception:
        pass
    tipo_map = {
        "separable":       ("Separable", "Separamos variables: f(y)dy = g(x)dx e integramos ambos lados."),
        "1st_linear":      ("Lineal 1er orden", "Forma: y' + P(x)y = Q(x). Factor integrante: mu = e^(int P dx)."),
        "Bernoulli":       ("Bernoulli", "Sustituimos v = y^(1-n) para linealizar."),
        "nth_linear_constant_coeff_homogeneous":
                           ("Lineal homogenea coef. constantes", "Resolvemos la ecuacion caracteristica."),
    }
    nombre, desc = tipo_map.get(hint, ("General", "Aplicamos el metodo de resolucion adecuado."))
    steps += [
        _step(f"Tipo: {nombre}", "method", desc,
              rf"\text{{Clasificacion: }}\texttt{{{hint}}}"),
        _step("Resolver la ODE", "calc",
              "Aplicamos el metodo y obtenemos la solucion general:",
              latex(sol)),
        _step("Solucion general", "result",
              "La solucion general (C1, C2 son constantes arbitrarias):",
              rf"\boxed{{{latex(sol)}}}"),
    ]
    return steps


import json as _json

@app.route("/api/compartir", methods=["POST"])
@login_required
def api_compartir():
    try:
        data   = request.json or {}
        token  = secrets.token_urlsafe(10)
        with get_db() as conn:
            conn.execute(
                "INSERT INTO shares (token,user,tool,input,result,method,steps) VALUES (?,?,?,?,?,?,?)",
                (token, session['user'], data.get('tool',''), data.get('input',''),
                 data.get('result',''), data.get('method',''), _json.dumps(data.get('steps',[])))
            )
            conn.commit()
        return jsonify({"url": f"{APP_URL}/s/{token}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/s/<token>")
def share_view(token):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM shares WHERE token=?", (token,)).fetchone()
    if not row:
        return "Solución no encontrada o expirada.", 404
    # Incrementar vistas (solo si no es el propio autor)
    if session.get('user') != row['user']:
        with get_db() as conn:
            conn.execute("UPDATE shares SET views = views + 1 WHERE token=?", (token,))
            conn.commit()
    steps = _json.loads(row['steps'])
    return render_template("share.html", row=row, steps=steps)


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "No encontrado"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Error interno"}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"success": False, "error": "Demasiadas solicitudes. Espera un momento antes de continuar."}), 429


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"\n{'='*60}")
    print(f"  CarlosTech Math AI v5.0")
    print(f"  http://localhost:{port}")
    print(f"{'='*60}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
