"""Lance l'app Fraud Hunter en une commande : python setup.py"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def step(n: int, label: str) -> None:
    print(f"[{n}/5] {label:<35}", end="", flush=True)


def ok() -> None:
    print("✓")


def fail(msg: str) -> None:
    print(f"\n\nErreur : {msg}")
    sys.exit(1)


# ── Étape 1 : version Python ────────────────────────────────────────────────
step(1, "Vérification de Python...")
if sys.version_info < (3, 9):
    fail(f"Python 3.9+ requis, version actuelle : {sys.version.split()[0]}")
ok()

# ── Étape 2 : environnement virtuel ─────────────────────────────────────────
step(2, "Création de l'environnement...")
env_dir = ROOT / "env"
if not env_dir.exists():
    result = subprocess.run(
        [sys.executable, "-m", "venv", str(env_dir)],
        capture_output=True,
    )
    if result.returncode != 0:
        fail(result.stderr.decode(errors="replace"))
ok()

# Chemin vers le Python de l'environnement virtuel
if sys.platform == "win32":
    venv_python = env_dir / "Scripts" / "python.exe"
    venv_streamlit = env_dir / "Scripts" / "streamlit.exe"
else:
    venv_python = env_dir / "bin" / "python"
    venv_streamlit = env_dir / "bin" / "streamlit"

if not venv_python.exists():
    fail(f"Python introuvable dans l'environnement virtuel : {venv_python}")

# ── Étape 3 : dépendances ───────────────────────────────────────────────────
step(3, "Installation des dépendances...")
req = ROOT / "requirements.txt"
if not req.exists():
    fail("requirements.txt introuvable à la racine du projet.")
result = subprocess.run(
    [str(venv_python), "-m", "pip", "install", "-r", str(req), "--quiet"],
    capture_output=True,
)
if result.returncode != 0:
    fail(result.stderr.decode(errors="replace"))
ok()

# ── Étape 4 : fichier .env ──────────────────────────────────────────────────
step(4, "Configuration .env...")
env_file = ROOT / ".env"
env_example = ROOT / ".env.example"
if not env_file.exists() and env_example.exists():
    shutil.copy(env_example, env_file)
    ok()
    print("      → .env créé depuis .env.example.")
    print("        Renseigne GEMINI_API_KEY dans .env pour les verdicts IA.")
    print("        Sans clé, l'app fonctionne avec un verdict de repli.")
else:
    ok()

# ── Étape 5 : lancement ─────────────────────────────────────────────────────
step(5, "Lancement de l'app...")
print()
app = ROOT / "src" / "ui" / "app.py"
if not app.exists():
    fail(f"Point d'entrée introuvable : {app}")

os.execv(
    str(venv_python),
    [str(venv_python), "-m", "streamlit", "run", str(app)],
)
