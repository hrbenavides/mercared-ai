#!/usr/bin/env python3
"""
MercaRed AI — Script de inicio rápido
Ejecuta: python start.py
"""
import subprocess, sys, os

BASE = os.path.dirname(os.path.abspath(__file__))

def instalar_dependencias():
    print("📦 Instalando dependencias...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "flask", "flask-login", "werkzeug", "-q"
    ])
    print("✅ Dependencias listas.\n")

def iniciar():
    from app import app, init_db
    print("🗄️  Inicializando base de datos SQLite...")
    with app.app_context():
        init_db()
    print("✅ Base de datos lista.\n")
    print("=" * 52)
    print("   🚀  MercaRed AI — Servidor iniciado")
    print("=" * 52)
    print()
    print("   🌐  Abre tu navegador en:")
    print("       http://127.0.0.1:5000")
    print()
    print("   🔑  Cuentas de prueba:")
    print("       Comprador  → comprador@demo.bo / demo123")
    print("       Vendedor   → vendedor@demo.bo  / demo123")
    print("       Transporte → transporte@demo.bo / demo123")
    print("       Admin      → admin@mercared.bo  / admin123")
    print()
    print("   ⏹   Presiona Ctrl+C para detener el servidor")
    print("=" * 52)
    print()
    app.run(debug=False, host="127.0.0.1", port=5000)

if __name__ == "__main__":
    os.chdir(BASE)
    try:
        import flask, flask_login
    except ImportError:
        instalar_dependencias()
    iniciar()
