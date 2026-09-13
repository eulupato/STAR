"""Prepara tradução neural offline opcional da STAR com Argos Translate.

Nada é baixado no startup da STAR. Este script é executado explicitamente pelo
usuário quando quiser materializar os modelos locais. O conjunto mínimo instala
pares bidirecionais entre inglês e PT/ES/IT/FR; o Argos pode fazer pivot por inglês
entre pares sem modelo direto.
"""
from __future__ import annotations

import argparse
import sys

PAIRS = (
    ("pt", "en"), ("en", "pt"),
    ("es", "en"), ("en", "es"),
    ("it", "en"), ("en", "it"),
    ("fr", "en"), ("en", "fr"),
)


def _load_argos():
    try:
        import argostranslate.package as package
    except (ImportError, OSError) as exc:
        raise SystemExit(
            "Argos Translate não está instalado. Instale o opcional com: "
            "python -m pip install -r requirements-translation.txt"
        ) from exc
    return package


def status(package) -> tuple[set[tuple[str, str]], list[str]]:
    installed = package.get_installed_packages()
    pairs = {(p.from_code, p.to_code) for p in installed if p.from_code and p.to_code}
    labels = sorted(f"{a}->{b}" for a, b in pairs)
    return pairs, labels


def install_missing(package) -> None:
    package.update_package_index()
    available = package.get_available_packages()
    installed, _ = status(package)
    missing = [pair for pair in PAIRS if pair not in installed]
    if not missing:
        print("Todos os pares mínimos da STAR já estão instalados.")
        return

    by_pair = {(p.from_code, p.to_code): p for p in available if p.from_code and p.to_code}
    unavailable = [pair for pair in missing if pair not in by_pair]
    if unavailable:
        formatted = ", ".join(f"{a}->{b}" for a, b in unavailable)
        raise SystemExit(f"Pares não encontrados no índice Argos atual: {formatted}")

    for pair in missing:
        model = by_pair[pair]
        print(f"Instalando {pair[0]} -> {pair[1]}...")
        path = model.download()
        package.install_from_path(path)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--install",
        action="store_true",
        help="baixa e instala explicitamente os oito pares mínimos",
    )
    args = parser.parse_args()

    package = _load_argos()
    if args.install:
        install_missing(package)

    installed, labels = status(package)
    required = set(PAIRS)
    print("STAR Offline Translation")
    print("Instalados:", ", ".join(labels) if labels else "nenhum")
    print(f"Cobertura mínima STAR: {len(required & installed)}/{len(required)} pares")
    print("Pronto para PT/EN/ES/IT/FR via inglês:", "SIM" if required <= installed else "NÃO")
    if not required <= installed:
        print("Execute novamente com --install quando quiser baixar os modelos.")


if __name__ == "__main__":
    main()
