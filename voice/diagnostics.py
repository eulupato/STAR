"""Diagnóstico da voz local da STAR V1.9."""
from __future__ import annotations

import sys
import time
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
    print(f"STT: {'PRONTO' if manager.stt_configured else 'NÃO INSTALADO'}")
    print(f"TTS rápido: {manager.tts_description}")

    try:
        import sounddevice as sd
        devices = sd.query_devices()
        outputs = [d for d in devices if int(d.get("max_output_channels", 0)) > 0]
        inputs = [d for d in devices if int(d.get("max_input_channels", 0)) > 0]
        print(f"Microfones disponíveis: {len(inputs)}")
        print(f"Saídas disponíveis: {len(outputs)}")
        if outputs:
            default_out = sd.default.device[1]
            print(f"Saída padrão: {default_out} — {sd.query_devices(default_out)['name']}")
        if inputs:
            default_in = sd.default.device[0]
            print(f"Entrada padrão: {default_in} — {sd.query_devices(default_in)['name']}")
    except Exception as exc:
        print(f"❌ Áudio do sistema indisponível: {type(exc).__name__}: {exc}")
        return 2

    print("\nPré-carregando STT/TTS (isso acontece uma vez por instalação)...")
    started = time.perf_counter()
    manager.warmup()
    print(f"Warmup concluído em {time.perf_counter() - started:.2f}s")
    if manager.last_error:
        print(f"⚠️ Warmup avisou: {manager.last_error}")

    print("\nTestando saída de voz. O teste usa Piper; se faltar o modelo, tenta a voz SAPI do Windows.")
    started = time.perf_counter()
    ok = manager.speak("Olá! Eu sou a STAR. Este é o teste da minha voz local.")
    elapsed = time.perf_counter() - started
    print(f"Tempo total TTS + reprodução: {elapsed:.2f}s")
    print(f"Motor usado: {manager.last_tts_engine}")
    if ok:
        print("✅ TESTE TTS + REPRODUÇÃO: OK")
        manager.close()
        return 0

    print(f"❌ TESTE TTS + REPRODUÇÃO: FALHOU\nDetalhe: {manager.last_error}")
    manager.close()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
