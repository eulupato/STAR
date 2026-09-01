"""Diagnóstico detalhado da voz local da STAR."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.release import RELEASE
from voice.manager import VoiceManager


def flag(value: bool) -> str:
    return "✅ OK" if value else "❌ AUSENTE"


def main() -> int:
    print("=" * 64)
    print(f"⭐ {RELEASE.label} — DIAGNÓSTICO DE VOZ")
    print("=" * 64)

    manager = VoiceManager()

    print(f"Modo de voz: {manager.mode.upper()}")
    print(f"Fallback automático: {'ATIVO' if manager.fallback_on_error else 'DESATIVADO'}")
    print(f"STT: {'PRONTO' if manager.stt_configured else 'NÃO INSTALADO'}")
    print()

    print("VOZ OFICIAL")
    print("-" * 64)
    print(f"Referência ativa: {manager.official.reference_path}")
    print(f"Arquivo: {manager.official.reference_path.name}")
    print(f"Referência existe: {flag(manager.official.reference_path.exists())}")
    if manager.official.reference_path.exists():
        size_mb = manager.official.reference_path.stat().st_size / (1024 * 1024)
        print(f"Tamanho da referência: {size_mb:.2f} MB")
    print(f"Ambiente Chatterbox: {flag(manager.official.python_path.exists())}")
    print(f"Worker Chatterbox: {flag(manager.official.worker_path.exists())}")
    print(f"Estado: {manager.official.status_message}")
    print()

    print("MODO RÁPIDO")
    print("-" * 64)
    print(f"Piper: {flag(manager.piper_configured)}")
    print(f"SAPI: {flag(manager.fallback.configured)}")
    print()

    print(f"TTS selecionado: {manager.tts_description}")

    try:
        import sounddevice as sd

        devices = sd.query_devices()
        outputs = [
            d for d in devices
            if int(d.get("max_output_channels", 0)) > 0
        ]
        inputs = [
            d for d in devices
            if int(d.get("max_input_channels", 0)) > 0
        ]
        print(f"Microfones disponíveis: {len(inputs)}")
        print(f"Saídas disponíveis: {len(outputs)}")

        if outputs:
            default_out = sd.default.device[1]
            print(
                f"Saída padrão: {default_out} — "
                f"{sd.query_devices(default_out)['name']}"
            )

        if inputs:
            default_in = sd.default.device[0]
            print(
                f"Entrada padrão: {default_in} — "
                f"{sd.query_devices(default_in)['name']}"
            )

    except Exception as exc:
        print(
            "❌ Áudio do sistema indisponível: "
            f"{type(exc).__name__}: {exc}"
        )
        return 2

    if manager.mode == "official" and not manager.official.configured:
        print()
        print("❌ A VOZ OFICIAL NÃO ESTÁ CONFIGURADA.")
        print(manager.official.status_message)
        print("Piper não será usado silenciosamente.")
        manager.close()
        return 3

    print()
    print("Pré-carregando motores necessários...")
    started = time.perf_counter()
    manager.warmup()
    warmup_elapsed = time.perf_counter() - started
    print(f"Warmup concluído em {warmup_elapsed:.2f}s")

    if manager.last_error:
        print(f"⚠️ Warmup: {manager.last_error}")

    if manager.mode == "official" and manager.last_error:
        print()
        print("❌ Chatterbox não ficou pronto.")
        print("Piper não será usado silenciosamente.")
        manager.close()
        return 4

    print()
    print("Gerando teste de voz...")
    started = time.perf_counter()
    ok = manager.speak(
        "Olá! Eu sou a STAR. Este é o teste da minha voz oficial."
    )
    elapsed = time.perf_counter() - started

    print(f"Tempo total TTS + reprodução: {elapsed:.2f}s")
    print(f"Motor usado: {manager.last_tts_engine}")

    if ok:
        print("✅ TESTE DE VOZ: OK")
        manager.close()
        return 0

    print("❌ TESTE DE VOZ: FALHOU")
    print(f"Detalhe: {manager.last_error}")
    manager.close()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
