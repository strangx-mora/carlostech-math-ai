#!/usr/bin/env python3
"""
Test final - Verifica que el servidor resuelve integrales
"""

import json
from server import app

# Crear cliente de prueba
client = app.test_client()

# Simular login
with client:
    # Primero hacer login
    response = client.post('/', data={
        'username': 'carlos',
        'password': 'carlos123'
    }, follow_redirects=True)
    
    print("=" * 60)
    print("TEST FINAL - SERVIDOR COMPLETO")
    print("=" * 60)
    
    # Pruebas de integrales
    test_cases = [
        ("x", "x^{2}/2"),
        ("2x", "x^{2}"),
        ("x**2", "x^{3}/3"),
        ("sin(x)", "-\\cos"),
        ("exp(x)", "e^{x}"),
    ]
    
    passed = 0
    failed = 0
    
    for expr, expected_part in test_cases:
        print(f"\nProbando: {expr}")
        
        response = client.post('/api/resolver', 
            json={'integral': expr},
            content_type='application/json'
        )
        
        data = response.get_json()
        
        if response.status_code == 200 and data.get('success'):
            result = data.get('result', '')
            print(f"  Resultado: {result}")
            print(f"  Metodo: {data.get('method_detected')}")
            print(f"  Tiempo: {data.get('computation_time')}")
            print("  OK")
            passed += 1
        else:
            print(f"  Error: {data.get('error')}")
            print(f"  Errores: {data.get('errors')}")
            print("  FALLO")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Resultados: {passed} OK | {failed} FAIL")
    print("=" * 60)
