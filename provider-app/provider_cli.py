from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from provider_app.cli import app

if __name__ == "__main__":
    app()
