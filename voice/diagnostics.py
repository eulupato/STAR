"""Diagnósticos da voz local da STAR V1.9 e do Voice V0.1 experimental."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def flag(value: bool) -> str:
    return "✅ OK" if value else "❌ AUSENTE"


def run_voice_diagnostic() -> int:
    """Preserva o diagnóstico oficial V1.9 existente."""
    from voice.manager import VoiceManager

    print("=" * 64)
    print("⭐ STAR V1.9 FINAL — DIAGNÓSTICO DE VOZ")
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
    ok = manager.speak("Olá! Eu sou a STAR. Este é o teste da minha voz oficial.")
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


def run_vad_diagnostic(duration_seconds: float | None = None) -> int:
    """Executa somente captura contínua + VAD + segmentação, sem STT/TTS/Core."""
    from voice.audio_input import AudioInputError, ContinuousAudioInput
    from voice.segmenter import SpeechEvent, SpeechSegmenter
    from voice.vad import SileroVAD, VADError

    print("=" * 64)
    print("⭐ STAR Voice V0.1 — DIAGNÓSTICO DE AUDIO + VAD")
    print("=" * 64)

    audio = ContinuousAudioInput()
    vad = SileroVAD()
    segmenter = SpeechSegmenter()

    print(f"Formato: {audio.samplerate} Hz · mono · float32 · {audio.blocksize} amostras/chunk")
    print(f"Fila limitada: {audio.max_chunks} chunks · ~{audio.buffer_memory_bytes / 1024:.1f} KiB PCM")
    print(f"Modelo local: {vad.model_path}")

    if not vad.configured:
        print("❌ VAD_MODEL_NOT_FOUND")
        print(f"Modelo ausente: {vad.model_path}")
        print("Execute: python -m voice.install_models")
        return 3

    try:
        started = time.perf_counter()
        vad.load()
        print(f"VAD: ONLINE · carregamento {1000 * (time.perf_counter() - started):.1f} ms")
        print("STATE: LISTENING")
        print("Pressione Ctrl+C para encerrar.")
        print()

        wall_start = time.perf_counter()
        cpu_start = time.process_time()
        audio.start()
        last_active_print = 0.0
        segment_count = 0

        while True:
            now = time.perf_counter()
            if duration_seconds is not None and now - wall_start >= duration_seconds:
                break

            audio_chunk = audio.read_chunk(timeout=0.5)
            if audio_chunk is None:
                if audio.last_error:
                    raise AudioInputError(audio.last_error)
                continue

            probability = vad.process_chunk(audio_chunk.samples)
            update = segmenter.feed(
                audio_chunk.samples,
                probability,
                timestamp_ms=audio_chunk.timestamp_ms,
            )

            if update.event == SpeechEvent.SPEECH_START:
                print(f"SPEECH START · p={probability:.3f}")
            elif update.event == SpeechEvent.SPEECH_ACTIVE:
                if now - last_active_print >= 1.0:
                    print(f"SPEECH ACTIVE · p={probability:.3f}")
                    last_active_print = now
            elif update.event == SpeechEvent.SPEECH_END and update.segment is not None:
                segment_count += 1
                print(
                    "SPEECH END · "
                    f"segment={segment_count} · duration={update.segment.duration_ms:.0f} ms · "
                    f"speech≈{update.segment.speech_duration_ms:.0f} ms"
                )
                print("segment created")
                print("STATE: LISTENING")
            elif update.event == SpeechEvent.SEGMENT_DROPPED:
                print("SEGMENT DROPPED · fala abaixo de min_speech_ms")

    except KeyboardInterrupt:
        print("\nEncerramento solicitado pelo usuário.")
    except (AudioInputError, VADError) as exc:
        print(f"❌ {type(exc).__name__}: {exc}")
        return 4
    except Exception as exc:
        print(f"❌ UNEXPECTED ERROR: {type(exc).__name__}: {exc}")
        return 5
    finally:
        audio.stop()

    elapsed = max(time.perf_counter() - wall_start, 1e-9)
    cpu_elapsed = max(time.process_time() - cpu_start, 0.0)
    cpu_process_percent = 100.0 * cpu_elapsed / elapsed
    final_segment = segmenter.flush()
    if final_segment is not None:
        segment_count += 1
        print(f"Segmento final no shutdown: {final_segment.duration_ms:.0f} ms")

    print()
    print("RESUMO")
    print("-" * 64)
    print(f"Tempo observado: {elapsed:.2f}s")
    print(f"Segmentos: {segment_count}")
    print(f"Chunks descartados por fila cheia: {audio.dropped_chunks}")
    print(f"CPU aproximada do processo no intervalo: {cpu_process_percent:.1f}%")
    print(f"Fila máxima PCM configurada: ~{audio.buffer_memory_bytes / 1024:.1f} KiB")
    print("RAM nativa adicional do ONNX: não medida por este diagnóstico.")
    print("✅ STAR Voice V0.1 diagnostic encerrado.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0].lower() == "vad":
        duration = None
        if len(args) > 1:
            try:
                duration = float(args[1])
            except ValueError:
                print("Uso: python -m voice.diagnostics vad [segundos]")
                return 64
            if duration <= 0:
                print("A duração deve ser positiva.")
                return 64
        return run_vad_diagnostic(duration)
    if args:
        print("Uso: python -m voice.diagnostics [vad [segundos]]")
        return 64
    return run_voice_diagnostic()


if __name__ == "__main__":
    raise SystemExit(main())
