"""Diagnóstico leve do STAR Vision Portal sem abrir a câmera."""
from pathlib import Path

from modules.vision import (
    PORTAL_FILTERS,
    dependencies_ready,
    dependency_status,
    filter_summary,
)

ROOT = Path(__file__).resolve().parent


def main():
    print("=" * 64)
    print("⭐ DIAGNÓSTICO STAR VISION PORTAL V1")
    print("=" * 64)

    failures = []
    client = ROOT / "clients" / "star_vision_portal.py"
    manifest = ROOT / "STAR_VISION_MANIFEST.json"
    optional_requirements = ROOT / "requirements-vision.txt"

    checks = [
        ("controlador modules/vision.py", (ROOT / "modules" / "vision.py").is_file()),
        ("cliente visual", client.is_file()),
        ("manifesto", manifest.is_file()),
        ("requirements opcionais", optional_requirements.is_file()),
        ("12 filtros únicos", len(PORTAL_FILTERS) == 12 and len({item["key"] for item in PORTAL_FILTERS}) == 12),
    ]
    for name, ok in checks:
        print(("🟢 " if ok else "🔴 ") + name)
        if not ok:
            failures.append(name)

    deps = dependency_status()
    for name, ok in deps.items():
        print(("🟢 " if ok else "🟡 ") + f"dependência opcional {name}")
    print(filter_summary())

    if not dependencies_ready():
        print("🟡 O Core funciona normalmente; para abrir a câmera execute: pip install -r requirements-vision.txt")

    if failures:
        print(f"❌ {len(failures)} falha(s) estrutural(is).")
        raise SystemExit(1)
    print("✅ Estrutura do STAR Vision Portal íntegra.")


if __name__ == "__main__":
    main()
