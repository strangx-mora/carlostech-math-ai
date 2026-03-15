#!/usr/bin/env python3
"""
Test parser - Verifica que el parser funciona correctamente
"""

from sympy import *
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, 
    implicit_multiplication_application, convert_xor
)
import re

def test_parser(expr_str):
    """Prueba el parser con una expresión"""
    print(f"\nProbando: {expr_str}")
    
    try:
        expr_text = expr_str.strip()
        expr_text = re.sub(r'\s+', '', expr_text)
        
        # Conversiones básicas
        expr_text = expr_text.replace("^", "**")
        expr_text = expr_text.replace("{", "(").replace("}", ")")
        
        # LaTeX fracciones
        expr_text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', expr_text)
        
        # LaTeX funciones
        expr_text = re.sub(r'\\sin\b', 'sin', expr_text)
        expr_text = re.sub(r'\\cos\b', 'cos', expr_text)
        expr_text = re.sub(r'\\tan\b', 'tan', expr_text)
        expr_text = re.sub(r'\\sqrt\b', 'sqrt', expr_text)
        expr_text = re.sub(r'\\log\b', 'log', expr_text)
        expr_text = expr_text.replace("\\ln", "log")
        expr_text = expr_text.replace("ln", "log")
        
        # Reemplazar π y ∞
        expr_text = expr_text.replace("π", "pi")
        expr_text = expr_text.replace("∞", "oo")
        
        # Reemplazar "e"
        expr_text = re.sub(r'\be([+\-*/()^])', r'E\1', expr_text)
        expr_text = re.sub(r'\be$', 'E', expr_text)
        
        # MULTIPLICACIÓN IMPLÍCITA
        expr_text = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr_text)
        expr_text = re.sub(r'(\))(\d)', r'\1*\2', expr_text)
        expr_text = re.sub(r'(\))([a-zA-Z])', r'\1*\2', expr_text)
        expr_text = re.sub(r'([a-zA-Z])(\()', lambda m: m.group(0) if m.group(1) in 'sincogtaelxp' else m.group(1) + '*' + m.group(2), expr_text)
        expr_text = re.sub(r'(\))(\()', r'\1*\2', expr_text)
        expr_text = re.sub(r'(\d)(\()', r'\1*\2', expr_text)
        
        print(f"   Convertido a: {expr_text}")
        
        # Parse
        transformations = (
            standard_transformations + 
            (implicit_multiplication_application, convert_xor)
        )
        
        local_dict = {
            'E': E,
            'pi': pi,
            'oo': oo,
            'sin': sin, 'cos': cos, 'tan': tan,
            'sinh': sinh, 'cosh': cosh, 'tanh': tanh,
            'asin': asin, 'acos': acos, 'atan': atan,
            'exp': exp, 'log': log, 'sqrt': sqrt,
        }
        
        expr = parse_expr(expr_text, local_dict=local_dict, transformations=transformations)
        print(f"   OK Parseado: {expr}")
        return True
        
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        return False

# Pruebas
print("=" * 60)
print("PRUEBAS DEL PARSER")
print("=" * 60)

test_cases = [
    "2x",
    "3*x",
    "x**2",
    "2x**2",
    "sin(x)",
    "2sin(x)",
    "x*sin(x)",
    "2*x*sin(x)",
    "sqrt(x)",
    "2sqrt(x)",
    "(x+1)**2",
    "2(x+1)",
    "sin(x)*cos(x)",
    "exp(x)",
    "2*exp(x)",
]

passed = 0
failed = 0

for test in test_cases:
    if test_parser(test):
        passed += 1
    else:
        failed += 1

print("\n" + "=" * 60)
print(f"Resultados: {passed} OK | {failed} FAIL")
print("=" * 60)
