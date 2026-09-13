"""Prepara tradução neural offline opcional da STAR com Argos Translate.

Nada é baixado no startup da STAR. Este script é executado explicitamente quando o
usuário quiser materializar modelos locais. Idiomas históricos ficam fora do Argos:
grego antigo, latim por eras e egípcio antigo usam léxico/corpora locais próprios.
"""
from __future__ import annotations

import argparse

# O inglês funciona como pivô entre pares quando não existe modelo direto. Árabe
# cobre MSA; ar-EG compartilha esse backend como fallback e mantém léxico dialetal
# separado no dicionário local.
MODERN_CODES = ("pt", "es", "it", "fr", "ja", "pl", "ko", "el", "ar")
PAIRS = tuple(pair for code in MODERN_CODES for pair in ((code, "en"), ("en", code)))


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
    return pairs, sorted(f"{a}->{b}" for a, b in pairs)


def install_missing(package) -> dict:
    """Instala somente pares realmente publicados no índice Argos atual.

    A ausência de um par não é erro fatal: a STAR continua funcional com catálogo
    estático/dicionário local e preserva o original quando não consegue traduzir a
    frase inteira. Isso evita que uma mudança externa do índice quebre o setup.
    """
    package.update_package_index()
    available = package.get_available_packages()
    installed, _ = status(package)
    missing = [pair for pair in PAIRS if pair not in installed]
    if not missing:
        print("Todos os pares modernos disponíveis para esta configuração já estão instalados.")
        return {"installed_now": [], "unavailable": []}

    by_pair = {(p.from_code, p.to_code): p for p in available if p.from_code and p.to_code}
    unavailable = [pair for pair in missing if pair not in by_pair]
    installable = [pair for pair in missing if pair in by_pair]
    installed_now = []

    for pair in installable:
        model = by_pair[pair]
        print(f"Instalando {pair[0]} -> {pair[1]}...")
        path = model.download()
        package.install_from_path(path)
        installed_now.append(pair)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

    if unavailable:
        formatted = ", ".join(f"{a}->{b}" for a, b in unavailable)
        print("Pares não publicados no índice Argos atual:", formatted)
        print("Esses pares permanecem no fallback offline de UI/dicionário sem alegar cobertura neural completa.")
    return {"installed_now": installed_now, "unavailable": unavailable}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true", help="baixa e instala explicitamente os pares modernos disponíveis")
    args = parser.parse_args()
    package = _load_argos()
    if args.install:
        install_missing(package)

    installed, labels = status(package)
    requested = set(PAIRS)
    print("STAR Offline Translation")
    print("Instalados:", ", ".join(labels) if labels else "nenhum")
    print(f"Cobertura solicitada STAR: {len(requested & installed)}/{len(requested)} pares")
    print("Runtime continua offline mesmo com cobertura parcial: SIM")
    print("Históricos (GRC/LA/EGY): léxico/corpus local, sem alegar MT moderno equivalente.")
    if not requested <= installed:
        print("Execute --install quando quiser materializar os modelos disponíveis; o startup nunca baixa modelos sozinho.")


if __name__ == "__main__":
    main()
