"""Seleção centralizada dos dispositivos de áudio locais da STAR.

A resolução prefere o dispositivo primário do Windows, que acompanha a saída
selecionada pelo usuário, em vez de prender a STAR a HDMI/TV ou outro endpoint.
Overrides explícitos: STAR_AUDIO_INPUT_DEVICE e STAR_AUDIO_OUTPUT_DEVICE.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
USER_SETTINGS = ROOT / "user_settings.json"

Direction = Literal["input", "output"]


def _channel_key(direction: Direction) -> str:
    return "max_input_channels" if direction == "input" else "max_output_channels"


def _env_key(direction: Direction) -> str:
    return "STAR_AUDIO_INPUT_DEVICE" if direction == "input" else "STAR_AUDIO_OUTPUT_DEVICE"


def _setting_key(direction: Direction) -> str:
    return "audio_input_device" if direction == "input" else "audio_output_device"


def _selector(direction: Direction) -> str:
    explicit = os.getenv(_env_key(direction), "").strip()
    if explicit:
        return explicit
    try:
        data = json.loads(USER_SETTINGS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return str(data.get(_setting_key(direction)) or "").strip()


def _available_indices(sd, direction: Direction) -> list[int]:
    key = _channel_key(direction)
    return [
        index for index, device in enumerate(sd.query_devices())
        if int(device.get(key, 0)) > 0
    ]
def _resolve_explicit(sd, direction: Direction, raw: str) -> int:
    available = _available_indices(sd, direction)
    value = str(raw or "").strip()
    if not value:
        raise ValueError("Seletor de dispositivo de áudio vazio.")

    try:
        index = int(value)
    except ValueError:
        index = None

    if index is not None:
        if index not in available:
            raise ValueError(
                f"Dispositivo de áudio {index} não possui canais de {direction}."
            )
        return index

    wanted = value.casefold()
    exact = [
        i for i in available
        if str(sd.query_devices(i)["name"]).casefold() == wanted
    ]
    if len(exact) == 1:
        return exact[0]

    partial = [
        i for i in available
        if wanted in str(sd.query_devices(i)["name"]).casefold()
    ]
    if len(partial) == 1:
        return partial[0]
    if not partial:
        raise ValueError(f"Dispositivo de áudio não encontrado: {value}")

    # O mesmo endpoint costuma aparecer em MME, DirectSound e WASAPI.
    # DirectSound é preferido porque aceita as taxas 16/22/24/44/48 kHz
    # usadas pelos motores atuais sem obrigar cada TTS a reamostrar.
    hostapis = sd.query_hostapis()
    direct = [
        i for i in partial
        if "directsound" in str(hostapis[int(sd.query_devices(i)["hostapi"])]["name"]).casefold()
    ]
    if direct:
        return direct[0]
    return partial[0]
def _windows_primary(sd, direction: Direction, available: list[int]) -> int | None:
    if sys.platform != "win32":
        return None

    preferred_names = (
        (
            "driver de captura de som primário",
            "primary sound capture driver",
            "mapeador de som da microsoft - input",
            "microsoft sound mapper - input",
        )
        if direction == "input"
        else (
            "driver de som primário",
            "primary sound driver",
            "mapeador de som da microsoft - output",
            "microsoft sound mapper - output",
        )
    )
    names = {
        i: str(sd.query_devices(i)["name"]).strip().casefold()
        for i in available
    }
    for preferred in preferred_names:
        for index, name in names.items():
            if name == preferred:
                return index
    return None


def resolve_audio_device(direction: Direction, sd_module=None) -> int:
    if direction not in {"input", "output"}:
        raise ValueError("direction deve ser 'input' ou 'output'.")

    if sd_module is None:
        import sounddevice as sd
    else:
        sd = sd_module
    explicit = _selector(direction)
    if explicit:
        return _resolve_explicit(sd, direction, explicit)

    available = _available_indices(sd, direction)
    if not available:
        raise RuntimeError(f"Nenhum dispositivo de áudio com canais de {direction}.")

    primary = _windows_primary(sd, direction, available)
    if primary is not None:
        return primary

    default = sd.default.device
    default_index = default[0] if direction == "input" else default[1]
    try:
        default_index = int(default_index)
    except (TypeError, ValueError):
        default_index = -1
    if default_index in available:
        return default_index

    return available[0]


def audio_device_info(direction: Direction, sd_module=None) -> dict:
    if sd_module is None:
        import sounddevice as sd
    else:
        sd = sd_module

    index = resolve_audio_device(direction, sd)
    device = sd.query_devices(index)
    return {
        "index": index,
        "name": str(device["name"]),
        "hostapi": int(device["hostapi"]),
        "default_samplerate": float(device["default_samplerate"]),
        "channels": int(device[_channel_key(direction)]),
        "override": _selector(direction) or None,
    }
