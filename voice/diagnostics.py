"""Diagnósticos da voz local da STAR V1.9 e do Voice V0.1 experimental."""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def flag(value: bool) -> str:
    return "✅ OK" if value else "❌ AUSENTE"


def _dbfs(amplitude: float) -> float:
    """Converte amplitude linear float32 em dBFS sem gerar -inf."""
    return 20.0 * math.log10(max(float(amplitude), 1e-12))


def list_audio_devices() -> int:
    """Lista entradas de áudio reais para diagnosticar seleção de microfone."""
    try:
        import sounddevice as sd

        devices = sd.query_devices()
        default_in = sd.default.device[0]
    except Exception as exc:
        print(f"❌ Áudio do sistema indisponível: {type(exc).__name__}: {exc}")
        return 2

    print("=" * 64)
    print("⭐ STAR — DISPOSITIVOS DE ENTRADA DE ÁUDIO")
    print("=" * 64)
    found = 0
    for index, device in enumerate(devices):
        if int(device.get("max_input_channels", 0)) <= 0:
            continue
        found += 1
        marker = "*" if index == default_in else " "
        print(
            f"{marker} [{index}] {device['name']} · "
            f"inputs={int(device.get('max_input_channels', 0))} · "
            f"default_sr={float(device.get('default_samplerate', 0.0)):.0f} Hz"
        )
    print()
    print(f"Entradas encontradas: {found}")
    print(f"* Entrada padrão atual: {default_in}")
    return 0


def _describe_input_device(device=None) -> tuple[object, str]:
    """Resolve índice/nome do dispositivo usado sem alterar a seleção global."""
    try:
        import sounddevice as sd

        selected = sd.default.device[0] if device is None else device
        info = sd.query_devices(selected, "input")
        return selected, str(info["name"])
    except Exception as exc:
        return device if device is not None else "desconhecido", (
            f"NÃO VERIFICADO ({type(exc).__name__}: {exc})"
        )


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


def run_vad_diagnostic(
    duration_seconds: float | None = None,
    device: int | None = None,
) -> int:
    """Executa captura + VAD + segmentação com telemetria de entrada, sem STT/TTS/Core."""
    import numpy as np

    from config import VAD_CONFIG
    from voice.audio_input import AudioInputError, ContinuousAudioInput
    from voice.segmenter import SpeechEvent, SpeechSegmenter
    from voice.vad import SileroVAD, VADError

    print("=" * 64)
    print("⭐ STAR Voice V0.1 — DIAGNÓSTICO DE AUDIO + VAD")
    print("=" * 64)

    audio = ContinuousAudioInput(device=device)
    vad = SileroVAD()
    segmenter = SpeechSegmenter()
    selected_device, selected_name = _describe_input_device(device)

    print(f"Entrada usada: [{selected_device}] {selected_name}")
    print(f"Formato: {audio.samplerate} Hz · mono · float32 · {audio.blocksize} amostras/chunk")
    print(f"Fila limitada: {audio.max_chunks} chunks · ~{audio.buffer_memory_bytes / 1024:.1f} KiB PCM")
    print(f"Modelo local: {vad.model_path}")
    print(f"Threshold VAD: {float(VAD_CONFIG['threshold']):.2f}")

    if not vad.configured:
        print("❌ VAD_MODEL_NOT_FOUND")
        print(f"Modelo ausente: {vad.model_path}")
        print("Execute: python -m voice.install_models")
        return 3

    chunk_count = 0
    segment_count = 0
    max_probability = 0.0
    max_peak = 0.0
    total_square_sum = 0.0
    total_samples = 0
    clipped_samples = 0
    window_square_sum = 0.0
    window_samples = 0
    window_peak = 0.0
    window_vad_max = 0.0

    try:
        started = time.perf_counter()
        vad.load()
        print(f"VAD: ONLINE · carregamento {1000 * (time.perf_counter() - started):.1f} ms")
        print("STATE: LISTENING")
        print("Telemetria INPUT será mostrada aproximadamente a cada 1 s.")
        print("Pressione Ctrl+C para encerrar.")
        print()

        wall_start = time.perf_counter()
        cpu_start = time.process_time()
        audio.start()
        last_active_print = 0.0
        last_level_print = wall_start

        while True:
            now = time.perf_counter()
            if duration_seconds is not None and now - wall_start >= duration_seconds:
                break

            audio_chunk = audio.read_chunk(timeout=0.5)
            if audio_chunk is None:
                if audio.last_error:
                    raise AudioInputError(audio.last_error)
                continue

            samples = np.asarray(audio_chunk.samples, dtype=np.float32)
            chunk_count += 1
            peak = float(np.max(np.abs(samples))) if samples.size else 0.0
            square_sum = float(np.dot(samples.astype(np.float64), samples.astype(np.float64)))
            max_peak = max(max_peak, peak)
            total_square_sum += square_sum
            total_samples += int(samples.size)
            clipped_samples += int(np.count_nonzero(np.abs(samples) >= 0.99))
            window_peak = max(window_peak, peak)
            window_square_sum += square_sum
            window_samples += int(samples.size)

            probability = vad.process_chunk(samples)
            max_probability = max(max_probability, probability)
            window_vad_max = max(window_vad_max, probability)
            update = segmenter.feed(
                samples,
                probability,
                timestamp_ms=audio_chunk.timestamp_ms,
            )

            if now - last_level_print >= 1.0 and window_samples:
                window_rms = math.sqrt(window_square_sum / window_samples)
                print(
                    "INPUT · "
                    f"rms={_dbfs(window_rms):.1f} dBFS · "
                    f"peak={_dbfs(window_peak):.1f} dBFS · "
                    f"vad_max={window_vad_max:.3f}"
                )
                window_square_sum = 0.0
                window_samples = 0
                window_peak = 0.0
                window_vad_max = 0.0
                last_level_print = now

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

    overall_rms = math.sqrt(total_square_sum / total_samples) if total_samples else 0.0
    peak_dbfs = _dbfs(max_peak)
    rms_dbfs = _dbfs(overall_rms)

    print()
    print("RESUMO")
    print("-" * 64)
    print(f"Entrada usada: [{selected_device}] {selected_name}")
    print(f"Tempo observado: {elapsed:.2f}s")
    print(f"Chunks processados: {chunk_count}")
    print(f"Segmentos: {segment_count}")
    print(f"Maior probabilidade VAD: {max_probability:.3f}")
    print(f"Nível RMS global: {rms_dbfs:.1f} dBFS")
    print(f"Pico de entrada: {peak_dbfs:.1f} dBFS")
    print(f"Amostras próximas de clipping: {clipped_samples}")
    print(f"Chunks descartados por fila cheia: {audio.dropped_chunks}")
    print(f"CPU aproximada do processo no intervalo: {cpu_process_percent:.1f}%")
    print(f"Fila máxima PCM configurada: ~{audio.buffer_memory_bytes / 1024:.1f} KiB")
    print("RAM nativa adicional do ONNX: não medida por este diagnóstico.")

    threshold = float(VAD_CONFIG["threshold"])
    print()
    print("DIAGNÓSTICO AUTOMÁTICO")
    print("-" * 64)
    if chunk_count == 0:
        print("❌ Nenhum chunk chegou ao consumidor. Verifique dispositivo/driver de entrada.")
    elif peak_dbfs < -55.0:
        print(
            "⚠️ A entrada ficou praticamente silenciosa. O mais provável é microfone "
            "errado/inativo, nível muito baixo ou dispositivo virtual selecionado."
        )
        print("Execute: python -m voice.diagnostics devices")
        print("Depois teste: python -m voice.diagnostics vad 30 <indice-do-microfone>")
    elif max_probability < threshold:
        print(
            "⚠️ Há sinal de áudio, mas o Silero não atingiu o threshold configurado. "
            "Não altere o threshold ainda: primeiro confirme o microfone e compare "
            "rms/peak/vad_max durante silêncio e fala."
        )
    elif segment_count == 0:
        print(
            "⚠️ O VAD cruzou o threshold, mas nenhum segmento foi produzido. "
            "Isso aponta para a etapa de segmentação e deve ser investigado antes de V0.2."
        )
    else:
        print("✅ Captura, VAD e segmentação produziram fala detectável neste teste.")

    print("✅ STAR Voice V0.1 diagnostic encerrado.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if args and args[0].lower() == "devices":
        if len(args) != 1:
            print("Uso: python -m voice.diagnostics devices")
            return 64
        return list_audio_devices()

    if args and args[0].lower() == "vad":
        duration = None
        device = None
        if len(args) > 3:
            print("Uso: python -m voice.diagnostics vad [segundos] [indice-do-microfone]")
            return 64
        if len(args) > 1:
            try:
                duration = float(args[1])
            except ValueError:
                print("Uso: python -m voice.diagnostics vad [segundos] [indice-do-microfone]")
                return 64
            if duration <= 0:
                print("A duração deve ser positiva.")
                return 64
        if len(args) > 2:
            try:
                device = int(args[2])
            except ValueError:
                print("O índice do microfone deve ser um número inteiro.")
                return 64
        return run_vad_diagnostic(duration, device)

    if args:
        print("Uso: python -m voice.diagnostics [devices | vad [segundos] [indice-do-microfone]]")
        return 64
    return run_voice_diagnostic()


if __name__ == "__main__":
    raise SystemExit(main())
