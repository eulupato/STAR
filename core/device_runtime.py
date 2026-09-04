"""Runtime adaptativo compartilhado pelos endpoints da STAR.

A fonte de verdade fica em STAR_MANIFEST.json. Clientes móveis não carregam
regras cognitivas: recebem apenas configuração de experiência, capacidades e
feature flags adequadas ao seu form factor.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import threading


_DEFAULT_ECOSYSTEM = {
    "schema": 1,
    "sync_interval_seconds": 30,
    "theme": {
        "background": "#080B12",
        "surface": "#111827",
        "primary": "#F6D35F",
        "secondary": "#F18ACB",
        "accent": "#6CC8FF",
        "text": "#FFFFFF",
        "muted": "#A8B0C0",
    },
    "labels": {
        "title": "STAR",
        "pair": "PAREAR",
        "send": "ENVIAR",
        "speak": "FALAR",
        "stop_and_send": "ENVIAR ÁUDIO",
        "camera": "MOSTRAR À STAR",
    },
    "features": {
        "text": True,
        "voice_input": True,
        "spoken_reply": True,
        "camera_transport": True,
        "vision_analysis": False,
        "remote_pc_actions": False,
    },
    "profiles": {
        "phone": {
            "layout": "comfortable",
            "show_connection_fields": True,
            "show_response_transcript": True,
            "preferred_columns": 1,
        },
        "watch": {
            "layout": "compact",
            "show_connection_fields": True,
            "show_response_transcript": True,
            "preferred_columns": 1,
        },
    },
}


def _merge(base, overlay):
    result = deepcopy(base)
    if not isinstance(overlay, dict):
        return result
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class DeviceRuntime:
    """Carrega e versiona a experiência comum de PC/mobile/watch."""

    def __init__(self, manifest_path: Path):
        self.manifest_path = Path(manifest_path)
        self._lock = threading.Lock()
        self._mtime_ns = None
        self._ecosystem = deepcopy(_DEFAULT_ECOSYSTEM)
        self._star_name = "STAR"
        self._star_version = "unknown"
        self._protocol = 1
        self._revision = "bootstrap"
        self._reload(force=True)

    def _reload(self, force: bool = False) -> None:
        try:
            stat = self.manifest_path.stat()
            mtime_ns = stat.st_mtime_ns
        except OSError:
            mtime_ns = None

        with self._lock:
            if not force and mtime_ns == self._mtime_ns:
                return

            manifest = {}
            if mtime_ns is not None:
                try:
                    manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    manifest = {}

            self._ecosystem = _merge(
                _DEFAULT_ECOSYSTEM,
                manifest.get("device_ecosystem") if isinstance(manifest, dict) else {},
            )
            self._star_name = str(manifest.get("name") or "STAR") if isinstance(manifest, dict) else "STAR"
            self._star_version = str(manifest.get("version") or "unknown") if isinstance(manifest, dict) else "unknown"
            gateway = manifest.get("device_gateway") if isinstance(manifest, dict) else {}
            if not isinstance(gateway, dict):
                gateway = {}
            try:
                self._protocol = int(gateway.get("protocol", 1))
            except (TypeError, ValueError):
                self._protocol = 1

            canonical = json.dumps(
                {
                    "name": self._star_name,
                    "version": self._star_version,
                    "protocol": self._protocol,
                    "ecosystem": self._ecosystem,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            self._revision = sha256(canonical).hexdigest()[:16]
            self._mtime_ns = mtime_ns

    @property
    def revision(self) -> str:
        self._reload()
        with self._lock:
            return self._revision

    def profile_for(self, device_record=None):
        self._reload()
        record = device_record if isinstance(device_record, dict) else {}
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        form_factor = str(metadata.get("form_factor") or "").strip().lower()

        with self._lock:
            ecosystem = deepcopy(self._ecosystem)
            revision = self._revision
            star_name = self._star_name
            star_version = self._star_version
            protocol = self._protocol

        profiles = ecosystem.get("profiles") if isinstance(ecosystem.get("profiles"), dict) else {}
        if form_factor not in profiles:
            name = str(record.get("name") or "").lower()
            form_factor = "watch" if "watch" in name or "relógio" in name else "phone"
        profile = profiles.get(form_factor) or profiles.get("phone") or {}

        return {
            "revision": revision,
            "schema": int(ecosystem.get("schema", 1)),
            "protocol": protocol,
            "sync_interval_seconds": max(10, int(ecosystem.get("sync_interval_seconds", 30))),
            "star": {"name": star_name, "version": star_version},
            "form_factor": form_factor,
            "theme": ecosystem.get("theme") if isinstance(ecosystem.get("theme"), dict) else {},
            "labels": ecosystem.get("labels") if isinstance(ecosystem.get("labels"), dict) else {},
            "features": ecosystem.get("features") if isinstance(ecosystem.get("features"), dict) else {},
            "profile": profile if isinstance(profile, dict) else {},
        }
