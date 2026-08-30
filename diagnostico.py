"""Diagnóstico offline da instalação da STAR."""

from pathlib import Path
import importlib

ROOT = Path(__file__).resolve().parent

MODULES = [
    "config",
    "core.star_identity",
    "core.internal_knowledge",
    "core.router",
    "core.executive",
    "core.star_core",
    "core.islands",
    "core.memory",
    "core.emotion",
    "core.avatar",
    "core.knowledge_registry",
    "core.cure",
    "database.database",
    "database.memory",
    "gui.app",
]


def main():
    print("=" * 60)
    print("⭐ DIAGNÓSTICO STAR V1.5")
    print("=" * 60)
    failures = []
    for name in MODULES:
        try:
            importlib.import_module(name)
            print(f"🟢 {name}")
        except Exception as error:
            failures.append((name, error))
            print(f"🔴 {name}: {error}")

    from main import create_star
    star = create_star()
    checks = [
        ("identidade", star.get_name() == "STAR"),
        ("criador", star.get_creator() == "Lu"),
        ("olá", bool(star.process("olá"))),
        ("nome sem artigo", bool(star.process("qual seu nome?"))),
        ("nome com artigo", bool(star.process("qual o seu nome?"))),
        ("nome com é", bool(star.process("qual é o seu nome?"))),
    ]
    for name, ok in checks:
        print(("🟢 " if ok else "🔴 ") + name)
        if not ok:
            failures.append((name, "check failed"))

    print("-" * 60)
    if failures:
        print(f"❌ {len(failures)} falha(s).")
        raise SystemExit(1)
    print("✅ DIAGNÓSTICO CONCLUÍDO SEM FALHAS.")


if __name__ == "__main__":
    main()
