"""Bridge de sensores físicos dos endpoints STAR para B25/B27.

Dispositivos somente reportam observações. Este módulo valida unidades/faixas,
normaliza proveniência e entrega evidência perceptiva ao B25. Dados de saúde não
viram diagnóstico; localização não concede permissão; medição só é aceita quando
o próprio hardware informa uma grandeza métrica.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import math
import time
from typing import Any


_ALLOWED_KINDS = {
    "location", "accelerometer", "gyroscope", "rotation_vector", "heart_rate",
    "steps", "proximity", "distance", "lidar_depth", "tof_distance", "rotary",
    "body_proprioception",
}


def _finite(value: Any, *, minimum: float | None = None, maximum: float | None = None) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("valor de sensor não finito")
    if minimum is not None and number < minimum:
        raise ValueError("valor de sensor abaixo da faixa")
    if maximum is not None and number > maximum:
        raise ValueError("valor de sensor acima da faixa")
    return number


def _timestamp(value: Any) -> str:
    now = time.time()
    if value is None:
        seconds = now
    else:
        raw = _finite(value)
        seconds = raw / 1000.0 if raw > 10_000_000_000 else raw
        # Rejeita telemetria muito antiga ou absurdamente futura; não corrige
        # silenciosamente o relógio do dispositivo.
        if seconds < now - 86_400 or seconds > now + 300:
            raise ValueError("timestamp do sensor fora da janela aceita")
    return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()


class DeviceSensorHub:
    """Normaliza lotes pequenos de telemetria autenticada para o B25."""

    MAX_BATCH = 64

    def __init__(self, star):
        self.star = star
        self.perception = star.multimodal_perception
        self.body = star.body_proprioception
        self.accepted = 0
        self.rejected = 0
        self.last_by_device: dict[str, dict] = {}

    @staticmethod
    def _vector(sample: dict, unit: str) -> dict:
        return {
            "x": _finite(sample.get("x"), minimum=-100_000, maximum=100_000),
            "y": _finite(sample.get("y"), minimum=-100_000, maximum=100_000),
            "z": _finite(sample.get("z"), minimum=-100_000, maximum=100_000),
            "unit": str(sample.get("unit") or unit)[:24],
        }

    def _normalize(self, sample: dict, *, device_id: str, capabilities: set[str]) -> tuple[str, dict]:
        if not isinstance(sample, dict):
            raise ValueError("amostra deve ser objeto")
        kind = str(sample.get("kind") or "").strip().lower()
        if kind not in _ALLOWED_KINDS:
            raise ValueError("tipo de sensor não suportado")
        timestamp = _timestamp(sample.get("timestamp"))
        source = f"device:{device_id}:{kind}"
        attrs = {"sensor_kind": kind, "device_id": device_id, "hardware_reported": True}
        event_key = str(sample.get("event_id") or f"{device_id}:{kind}:{timestamp}")[:180]

        if kind == "location":
            lat = _finite(sample.get("latitude"), minimum=-90, maximum=90)
            lon = _finite(sample.get("longitude"), minimum=-180, maximum=180)
            accuracy = _finite(sample.get("accuracy_m", 0), minimum=0, maximum=100_000)
            attrs.update({"latitude": lat, "longitude": lon, "accuracy_m": accuracy, "privacy": "ephemeral_observation"})
            observation = {
                "content": f"Localização física reportada pelo dispositivo com precisão aproximada de {accuracy:.1f} m",
                "timestamp": timestamp, "confidence": 0.95 if accuracy <= 25 else 0.75,
                "importance": 0.65, "event_key": event_key, "attributes": attrs,
            }
            return "location", observation

        if kind in {"accelerometer", "gyroscope", "rotation_vector"}:
            defaults = {"accelerometer": "m/s^2", "gyroscope": "rad/s", "rotation_vector": "unitless"}
            vector = self._vector(sample, defaults[kind])
            attrs.update(vector)
            observation = {
                "content": f"{kind} físico atualizado",
                "timestamp": timestamp, "confidence": 0.98, "importance": 0.45,
                "event_key": event_key, "attributes": attrs,
            }
            return "movement", observation

        if kind == "heart_rate":
            bpm = _finite(sample.get("bpm"), minimum=20, maximum=260)
            accuracy = str(sample.get("accuracy") or "unknown")[:24]
            attrs.update({"bpm": bpm, "accuracy": accuracy, "health_data": True, "diagnosis": False})
            observation = {
                "content": f"Frequência cardíaca observada pelo sensor: {bpm:.0f} bpm",
                "timestamp": timestamp, "confidence": 0.9, "importance": 0.65,
                "event_key": event_key, "attributes": attrs,
            }
            return "sensor", observation

        if kind == "steps":
            steps = int(_finite(sample.get("steps"), minimum=0, maximum=10_000_000))
            attrs.update({"steps": steps, "health_data": True, "diagnosis": False})
            return "sensor", {
                "content": f"Contagem física de passos reportada: {steps}",
                "timestamp": timestamp, "confidence": 0.9, "importance": 0.4,
                "event_key": event_key, "attributes": attrs,
            }

        if kind in {"proximity", "distance", "lidar_depth", "tof_distance"}:
            meters = sample.get("meters")
            if meters is None and sample.get("centimeters") is not None:
                meters = _finite(sample.get("centimeters"), minimum=0, maximum=100_000) / 100.0
            meters = _finite(meters, minimum=0, maximum=10_000)
            method = str(sample.get("method") or kind)[:48]
            attrs.update({"meters": meters, "method": method, "metric_measurement": True, "simulated": False})
            return "sensor", {
                "content": f"Medição física {method}: {meters:.3f} m",
                "timestamp": timestamp, "confidence": 0.9, "importance": 0.55,
                "event_key": event_key, "attributes": attrs,
            }

        if kind == "rotary":
            delta = _finite(sample.get("delta"), minimum=-100, maximum=100)
            attrs.update({"delta": delta, "input": "physical_rotary", "operational_authorization": False})
            return "sensor", {
                "content": f"Entrada física da coroa/bezel: {delta:+.3f}",
                "timestamp": timestamp, "confidence": 0.99, "importance": 0.35,
                "event_key": event_key, "attributes": attrs,
            }

        if kind == "body_proprioception":
            state = sample.get("state")
            if not isinstance(state, dict):
                raise ValueError("body_proprioception requer state")
            # B27 é o único dono do estado corporal; o hub apenas encaminha.
            body_state = self.body.update_proprioception(
                source=f"device:{device_id}",
                position=state.get("position"), orientation=state.get("orientation"),
                movement=state.get("movement"), energy=state.get("energy"),
                joints=state.get("joints"), servos=state.get("servos"), sensors=state.get("sensors"),
            )
            return "sensor", {
                "content": "Propriocepção física encaminhada ao B27",
                "timestamp": timestamp, "confidence": 0.95, "importance": 0.7,
                "event_key": event_key,
                "attributes": {**attrs, "b27_updated": True, "state_timestamp": body_state.get("timestamp")},
            }

        raise ValueError(kind)

    def ingest(self, device_id: str, payload: dict, *, capabilities=()) -> dict:
        device_id = str(device_id or "").strip()[:80]
        if not device_id:
            raise ValueError("device_id ausente")
        samples = payload.get("samples") if isinstance(payload, dict) else None
        if samples is None and isinstance(payload, dict) and payload.get("kind"):
            samples = [payload]
        if not isinstance(samples, list) or not samples:
            raise ValueError("telemetria requer samples")
        if len(samples) > self.MAX_BATCH:
            raise ValueError("lote de sensores acima do limite")
        caps = {str(value).strip().lower() for value in (capabilities or ()) if str(value).strip()}
        accepted, rejected = [], []
        for index, sample in enumerate(samples):
            try:
                modality, observation = self._normalize(sample, device_id=device_id, capabilities=caps)
                item = self.perception.ingest(modality, observation, source=f"device:{device_id}")
                accepted.append(item)
                self.accepted += 1
                self.last_by_device[device_id] = deepcopy(item)
            except (TypeError, ValueError, KeyError) as exc:
                self.rejected += 1
                rejected.append({"index": index, "reason": str(exc)[:160]})
        proactive = getattr(self.star, "proactivity", None)
        if accepted and proactive is not None:
            proactive.emit(
                "device_sensor_update",
                f"{len(accepted)} observação(ões) físicas recebidas de {device_id}",
                payload={"device_id": device_id, "observation_ids": [x["observation_id"] for x in accepted]},
                importance=0.25,
                notify=False,
            )
        return {
            "device_id": device_id,
            "accepted": len(accepted),
            "rejected": rejected,
            "observations": accepted,
            "operational_authorization": False,
            "simulated": False,
        }

    def status(self) -> dict:
        return {
            "accepted": self.accepted,
            "rejected": self.rejected,
            "devices_seen": len(self.last_by_device),
            "supported_kinds": tuple(sorted(_ALLOWED_KINDS)),
            "real_sensor_data_only": True,
            "health_diagnosis": False,
            "sensor_data_grants_permission": False,
        }
