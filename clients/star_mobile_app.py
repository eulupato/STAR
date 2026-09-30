"""STAR Mobile simulator: mesma STAR, superfície compacta sem Ilhas."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import run_surface


def main():
    return run_surface("mobile")


if __name__ == "__main__":
    raise SystemExit(main())
