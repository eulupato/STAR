"""Smoke test manual da STAR V2.0 MIND."""

from main import create_star


def main():
    star = create_star()
    print("MIND:", star.mind_status())
    print("STAR:", star.process("olá"))
    print("MATH:", star.process("quanto é 2+2"))
    print("DIAGNÓSTICO:", star.process("diagnóstico da mente"))


if __name__ == "__main__":
    main()
