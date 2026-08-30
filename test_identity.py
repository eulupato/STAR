from core.star_identity import StarIdentity


def main():

    print("=" * 60)
    print("⭐ STAR — IDENTITY CORE TEST")
    print("=" * 60)

    identity = StarIdentity()

    print()
    print("Nome:")
    print(identity.get_name())

    print()
    print("Nome completo:")
    print(identity.get_full_name())

    print()
    print("Criador:")
    print(identity.get_creator())

    print()
    print("Lu é o criador?")
    print(identity.is_creator("Lu"))

    print()
    print("João é o criador?")
    print(identity.is_creator("João"))

    print()
    print("Princípios:")

    for principle in identity.get_principles():

        print(
            f"  • {principle}"
        )

    print()
    print("=" * 60)
    print("IDENTIDADE CARREGADA")
    print("=" * 60)


if __name__ == "__main__":
    main()