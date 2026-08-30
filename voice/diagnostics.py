"""Diagnóstico da voz local da STAR.

Este teste verifica STT, TTS, dispositivo de saída e executa uma fala real.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voice.manager import VoiceManager


def main() -> int:
    print("=" * 60)
    print("⭐ STAR V1.9 — DIAGNÓSTICO DA VOZ LOCAL")
    print("=" * 60)

    manager = VoiceManager()
    print(f"STT instalado: {'SIM' if manager.stt_configured else 'NÃO'}")
    print(f"Chatterbox configurado: {'SIM' if manager.configured else 'NÃO'}")

    try:
        import sounddevice as sd
        outputs = [d for d in sd.query_devices() if int(d.get("max_output_channels", 0)) > 0]
        print(f"Dispositivos de saída: {len(outputs)}")
        if outputs:
            default_out = sd.default.device[1]
            print(f"Saída padrão: {default_out} — {sd.query_devices(default_out)['name']}")
        else:
            print("ERRO: nenhum dispositivo de saída encontrado.")
    except Exception as exc:
        print(f"ERRO no dispositivo de áudio: {type(exc).__name__}: {exc}")
        return 2

    print("\nGerando fala de teste. Na primeira execução, o Chatterbox pode demorar para carregar.")
    ok = manager.speak("Olá! Eu sou a STAR. Este é o teste do meu sistema de voz local.")
    if ok:
        print("\n✅ TESTE TTS + REPRODUÇÃO: OK")
        manager.close()
        return 0

    print(f"\n❌ TESTE TTS + REPRODUÇÃO: FALHOU\nDetalhe: {manager.last_error}")
    manager.close()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
