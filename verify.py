#!/usr/bin/env python3
"""
Script de verificación rápida - CarlosTech Math AI
Verifica que todo esté configurado correctamente
"""

import os
import sys

def check_environment():
    """Verifica variables de entorno"""
    print("🔍 Verificando variables de entorno...")
    
    secret_key = os.environ.get('SECRET_KEY')
    gemini_key = os.environ.get('GEMINI_API_KEY')
    
    if secret_key:
        print("  ✅ SECRET_KEY configurada")
    else:
        print("  ⚠️  SECRET_KEY no configurada (usando default)")
    
    if gemini_key:
        print("  ✅ GEMINI_API_KEY configurada")
    else:
        print("  ⚠️  GEMINI_API_KEY no configurada (IA deshabilitada)")
    
    return True

def check_files():
    """Verifica archivos necesarios"""
    print("\n📁 Verificando archivos...")
    
    required_files = [
        'server.py',
        'requirements.txt',
        'templates/index.html',
        'templates/login.html',
        'static/style.css',
        '.env.example'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - FALTA")
            all_exist = False
    
    return all_exist

def check_dependencies():
    """Verifica dependencias instaladas"""
    print("\n📦 Verificando dependencias...")
    
    dependencies = [
        'flask',
        'sympy',
        'numpy',
        'google.generativeai'
    ]
    
    all_installed = True
    for dep in dependencies:
        try:
            __import__(dep.replace('.', '_'))
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep} - NO INSTALADO")
            all_installed = False
    
    return all_installed

def main():
    print("=" * 60)
    print("🚀 CarlosTech Math AI - Verificación Rápida")
    print("=" * 60)
    
    env_ok = check_environment()
    files_ok = check_files()
    deps_ok = check_dependencies()
    
    print("\n" + "=" * 60)
    print("📊 Resumen:")
    print("=" * 60)
    
    if env_ok and files_ok and deps_ok:
        print("✅ TODO ESTÁ LISTO")
        print("\n🚀 Para ejecutar:")
        print("   python server.py")
        print("\n📍 Acceder a:")
        print("   http://localhost:10000")
        print("\n👤 Credenciales:")
        print("   Usuario: carlos")
        print("   Contraseña: carlos123")
        return 0
    else:
        print("❌ HAY PROBLEMAS")
        if not deps_ok:
            print("\n📦 Instalar dependencias:")
            print("   pip install -r requirements.txt")
        if not files_ok:
            print("\n📁 Verifica que todos los archivos existan")
        return 1

if __name__ == "__main__":
    sys.exit(main())
