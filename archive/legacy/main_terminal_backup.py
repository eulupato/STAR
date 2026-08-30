from core.star_core import StarCore
from core.router import Router
from core.executive import Executive
from core.state import StarState
from core.models.model_manager import ModelManager
from core.models.local.ollama import OllamaModel


def main():

    print("=" * 60)
    print("⭐ INICIALIZANDO STAR")
    print("=" * 60)

    # =========================================================
    # ESTADO
    # =========================================================

    state = StarState()

    # =========================================================
    # ROUTER
    # =========================================================

    router = Router()

    # =========================================================
    # OLLAMA
    # =========================================================
    # O Ollama é opcional.
    # A STAR continua existindo sem ele.

    ollama = OllamaModel(
        model_name="qwen3:8b",
        host="http://127.0.0.1:11434",
    )

    ollama_available = ollama.is_available()

    if ollama_available:

        print("🟢 Ollama conectado.")

        model_manager = ModelManager(
            local_model=ollama
        )

    else:

        print("🟡 Ollama não disponível.")
        print("   STAR continuará funcionando sem modelo externo.")

        model_manager = ModelManager(
            local_model=None
        )

    # =========================================================
    # EXECUTIVO
    # =========================================================

    executive = Executive(
        model_manager=model_manager
    )

    # =========================================================
    # STAR CORE
    # =========================================================

    star = StarCore(
        router=router,
        executive=executive,
        state=state,
    )

    # =========================================================
    # STAR ONLINE
    # =========================================================

    print()
    print("=" * 60)
    print("⭐ STAR ONLINE")
    print("=" * 60)
    print()

    print(f"🧠 Identidade: {star.get_name()}")
    print(f"👤 Criador: {star.get_creator()}")
    print(
        "🤖 Modelo externo:",
        "ATIVO" if ollama_available else "INATIVO"
    )

    print()

    # =========================================================
    # LOOP
    # =========================================================

    while True:

        try:

            user_input = input("Lu > ").strip()

        except KeyboardInterrupt:

            print()
            print("Encerrando STAR...")
            break

        except EOFError:

            print()
            print("Encerrando STAR...")
            break

        if not user_input:
            continue

        if user_input.lower() in {
            "sair",
            "exit",
            "quit",
        }:

            print()
            print("⭐ Até logo, Lu.")
            break

        try:

            response = star.process(
                user_input
            )

            print()
            print(f"STAR > {response}")
            print()

        except Exception as error:

            print()
            print("❌ ERRO NO PROCESSAMENTO:")
            print(error)
            print()


if __name__ == "__main__":
    main()