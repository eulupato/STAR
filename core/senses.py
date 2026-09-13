"""Contrato unificado de observações para STAR Senses.

Esta camada não declara percepção semântica que ainda não existe. Ela normaliza
entradas de câmera/tela/sensores para que MIND e Device Gateway possam consumi-las
sem criar formatos paralelos.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Observation:
    modality: str
    source: str
    payload: dict
    confidence: float = 1.0
    timestamp: str = ""
    provenance: dict | None = None

    def normalized(self) -> dict:
        data = asdict(self)
        data["timestamp"] = self.timestamp or _now()
        data["confidence"] = max(0.0, min(float(self.confidence), 1.0))
        data["provenance"] = self.provenance or {}
        raw = json.dumps({k: data[k] for k in ("modality", "source", "payload", "timestamp")}, sort_keys=True, default=str)
        data["observation_id"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
        return data


class SensorFusionBuffer:
    def __init__(self, max_items: int = 256):
        self.items = deque(maxlen=max(16, min(int(max_items), 4096)))

    def ingest(self, observation: Observation | dict) -> dict:
        data = observation.normalized() if isinstance(observation, Observation) else dict(observation)
        data.setdefault("timestamp", _now()); data.setdefault("confidence", 1.0); data.setdefault("provenance", {})
        self.items.append(data); return data

    def recent(self, *, modality: str | None = None, limit: int = 20) -> list[dict]:
        values = list(self.items)
        if modality:
            values = [x for x in values if x.get("modality") == modality]
        return values[-max(1, min(int(limit), 500)):]

    def fuse_snapshot(self) -> dict:
        latest = {}
        for item in self.items:
            latest[item.get("modality", "unknown")] = item
        return {"timestamp": _now(), "modalities": sorted(latest), "latest": latest,
                "semantic_scene_understanding": False}


class LocalImageObservation:
    @staticmethod
    def from_path(path: str | Path, *, source: str = "local-file") -> Observation:
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        return Observation("image", source, {"path": str(path), "size": path.stat().st_size}, 1.0,
                           provenance={"local_only": True, "semantic_analysis": False})


def senses_stats() -> dict:
    return {"status": "foundation", "observation_contract": True, "fusion_buffer": True,
            "vision_portal_bridge_ready": True, "screen_awareness_semantic": False,
            "multimodal_semantic_fusion": False}
