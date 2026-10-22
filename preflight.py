"""Verificações locais antes da apresentação: python preflight.py."""
from pathlib import Path
import json
import subprocess
import sys
from app.specialist.engine import load_knowledge_base
root = Path(__file__).resolve().parent
checks = [root / "templates/index.html", root / "static/app.js", root / "static/dashboard-final.css", root / "static/hero-cow.jpg", root / "knowledge/rules.json", root / "knowledge/questions.json"]
for path in checks:
    print(("OK" if path.is_file() else "FALTA"), path.relative_to(root))
if not all(path.is_file() for path in checks):
    sys.exit(1)
kb = load_knowledge_base(root / "knowledge/rules.json")
print(f"Base: {kb['version']} | {len(kb['rules'])} regras | {len(kb['sources'])} fontes cadastradas")
print("Executando testes...")
status = subprocess.call([sys.executable, "-m", "pytest", "-q"], cwd=root)
print("PASSOU: testes automatizados" if status == 0 else "FALHOU: testes automatizados")
print("PENDENTE: ensaio visual no navegador, rede localhost e revisão veterinária das regras.")
sys.exit(status)
