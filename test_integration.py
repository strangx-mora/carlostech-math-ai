#!/usr/bin/env python3
"""
Test de integración - Prueba el motor completo de resolución
"""

from sympy import *
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, 
    implicit_multiplication_application, convert_xor
)
from sympy.integrals import integrate as sympy_integrate
import re
import time

x = symbols('x')

def parse_input(expr_str):
    """Parse varios formatos de entrada"""
    try:
        expr_text = expr_str.strip()
        expr_text = re.sub(r'\s+', '', expr_text)
        
        # Conversiones básicas
        expr_text = expr_text.replace("^", "**")
        expr_text = expr_text.replace("{", "(").replace("}", ")")
        
        # LaTeX
        expr_text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', expr_text)
        expr_text = expr_text.replace("\\sin", "sin")
        expr_text = expr_text.replace("\\cos", "cos")
        expr_text = expr_text.replace("\\tan", "tan")
        expr_text = expr_text.replace("\\sqrt", "sqrt")
        expr_text = expr_text.replace("\\log", "log")
        expr_text = expr_text.replace("\\ln", "log")
        expr_text = expr_text.replace("ln", "log")
        
        # Constantes
        expr_text = expr_text.replace("π", "pi")
        expr_text = expr_text.replace("∞", "oo")
        
        # Multiplicación implícita
        expr_text = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr_text)
        expr_text = re.sub(r'(\))(\d)', r'\1*\2', expr_text)
        expr_text = re.sub(r'(\))([a-zA-Z])', r'\1*\2', expr_text)
        expr_text = re.sub(r'(\d)(\()', r'\1*\2', expr_text)
        expr_text = re.sub(r'(\))(\()', r'\1*\2', expr_text)
        
        # Reemplazar e
        expr_text = re.sub(r'\be([+\-*/()^]|$)', r'E\1', expr_text)
        
        print(f"   Convertido: {expr_text}")
        
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
        print(f"   Parseado: {expr}")
        return expr
        
    except Exception as e:
        print(f"   ERROR en parsing: {str(e)}")
        return None

def test_integral(expr_str):
    """Prueba resolver una integral"""
    print(f"\nResolviendo: {expr_str}")
    
    # Parse
    expr = parse_input(expr_str)
    if expr is None:
        print("   FALLO: No se pudo parsear")
        return False
    
    # Resolver
    try:
        start = time.time()
        result = sympy_integrate(expr, x)
        elapsed = time.time() - start
        
        print(f"   Resultado: {result}")
        print(f"   LaTeX: {latex(result)}")
        print(f"   Tiempo: {elapsed:.3f}s")
        
        if result is None or result == oo or result == -oo:
            print("   FALLO: Resultado inválido")
            return False
        
        print("   OK")
        return True
        
    except Exception as e:
        print(f"   ERROR en integración: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Pruebas
print("=" * 60)
print("TEST DE INTEGRACION - MOTOR COMPLETO")
print("=" * 60)

test_cases = [
    "x",
    "2x",
    "x**2",
    "2x**2",
    "x**3",
    "sin(x)",
    "cos(x)",
    "exp(x)",
    "1/x",
    "sqrt(x)",
]

passed = 0
failed = 0

for test in test_cases:
    if test_integral(test):
        passed += 1
    else:
        failed += 1

print("\n" + "=" * 60)
print(f"Resultados: {passed} OK | {failed} FAIL")
print("=" * 60)
