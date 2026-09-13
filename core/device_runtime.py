"""Runtime adaptativo compartilhado pelos endpoints da STAR.

A fonte de verdade fica em STAR_MANIFEST.json. Clientes móveis não carregam regras
cognitivas e recebem tema, capacidades e rótulos já localizados conforme o mesmo
locale persistido pelo Core.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import threading

from core.global_localization import GlobalLocalizationEngine
from core.language_profiles import DEFAULT_LOCALE, LOCALES


_DEFAULT_ECOSYSTEM = {
    "schema": 1,
    "sync_interval_seconds": 30,
    "theme": {
        "background": "#080B12", "surface": "#111827", "primary": "#F6D35F",
        "secondary": "#F18ACB", "accent": "#6CC8FF", "text": "#FFFFFF", "muted": "#A8B0C0",
    },
    "labels": {
        "title": "STAR", "pair": "PAREAR", "send": "ENVIAR", "speak": "FALAR",
        "stop_and_send": "ENVIAR ÁUDIO", "camera": "MOSTRAR À STAR", "now": "AGORA",
        "search": "BUSCA", "health": "SAÚDE", "weather": "CLIMA", "language": "IDIOMA",
    },
    "features": {
        "text": True, "voice_input": True, "spoken_reply": True, "camera_transport": True,
        "vision_analysis": False, "remote_pc_actions": False, "now_page": True,
    },
    "profiles": {
        "phone": {"layout": "comfortable", "show_connection_fields": True, "show_response_transcript": True, "preferred_columns": 1},
        "watch": {"layout": "compact", "show_connection_fields": True, "show_response_transcript": True, "preferred_columns": 1},
    },
}


def _merge(base, overlay):
    result = deepcopy(base)
    if not isinstance(overlay, dict): return result
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict): result[key] = _merge(result[key], value)
        else: result[key] = deepcopy(value)
    return result


class DeviceRuntime:
    """Carrega/versiona a experiência comum de PC/mobile/watch."""

    def __init__(self, manifest_path: Path):
        self.manifest_path = Path(manifest_path)
        self.language_settings = self.manifest_path.parent / "runtime" / "language" / "settings.json"
        self.localization = GlobalLocalizationEngine()
        self._lock = threading.Lock()
        self._source_digest = None
        self._ecosystem = deepcopy(_DEFAULT_ECOSYSTEM)
        self._star_name = "STAR"
        self._star_version = "unknown"
        self._protocol = 1
        self._revision = "bootstrap"
        self._reload(force=True)

    def _active_locale(self) -> str:
        try:
            data = json.loads(self.language_settings.read_text(encoding="utf-8"))
            locale = str(data.get("locale") or DEFAULT_LOCALE)
            return locale if locale in LOCALES else DEFAULT_LOCALE
        except (OSError, json.JSONDecodeError, AttributeError):
            return DEFAULT_LOCALE

    def _localized_labels(self, labels: dict, locale: str) -> dict:
        result = {}
        for key, value in labels.items():
            text = str(value)
            translated = self.localization.static(text, locale)
            result[str(key)] = translated if translated is not None else text
        return result

    def _reload(self, force: bool = False) -> None:
        try: raw = self.manifest_path.read_bytes()
        except OSError: raw = b""
        source_digest = sha256(raw).hexdigest()
        with self._lock:
            if not force and source_digest == self._source_digest: return
        if raw:
            try: manifest = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError): return
        else: manifest = {}
        if not isinstance(manifest, dict): manifest = {}
        ecosystem = _merge(_DEFAULT_ECOSYSTEM, manifest.get("device_ecosystem") if isinstance(manifest, dict) else {})
        star_name = str(manifest.get("name") or "STAR")
        star_version = str(manifest.get("version") or "unknown")
        gateway = manifest.get("device_gateway")
        if not isinstance(gateway, dict): gateway = {}
        try: protocol = int(gateway.get("protocol", 1))
        except (TypeError, ValueError): protocol = 1
        canonical = json.dumps({"name":star_name,"version":star_version,"protocol":protocol,"ecosystem":ecosystem}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        revision = sha256(canonical).hexdigest()[:16]
        with self._lock:
            self._ecosystem=ecosystem; self._star_name=star_name; self._star_version=star_version
            self._protocol=protocol; self._revision=revision; self._source_digest=source_digest

    @property
    def revision(self) -> str:
        self._reload()
        with self._lock: return self._revision

    def profile_for(self, device_record=None):
        self._reload()
        record = device_record if isinstance(device_record, dict) else {}
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        form_factor = str(metadata.get("form_factor") or "").strip().lower()
        with self._lock:
            ecosystem=deepcopy(self._ecosystem); revision=self._revision; star_name=self._star_name
            star_version=self._star_version; protocol=self._protocol
        profiles = ecosystem.get("profiles") if isinstance(ecosystem.get("profiles"), dict) else {}
        if form_factor not in profiles:
            name = str(record.get("name") or "").lower()
            form_factor = "watch" if "watch" in name or "relógio" in name else "phone"
        profile = profiles.get(form_factor) or profiles.get("phone") or {}
        locale = self._active_locale()
        locale_meta = LOCALES[locale]
        raw_labels = ecosystem.get("labels") if isinstance(ecosystem.get("labels"), dict) else {}
        return {
            "revision": revision,
            "schema": int(ecosystem.get("schema", 1)),
            "protocol": protocol,
            "sync_interval_seconds": max(10, int(ecosystem.get("sync_interval_seconds", 30))),
            "star": {"name": star_name, "version": star_version},
            "form_factor": form_factor,
            "theme": ecosystem.get("theme") if isinstance(ecosystem.get("theme"), dict) else {},
            "labels": self._localized_labels(raw_labels, locale),
            "features": ecosystem.get("features") if isinstance(ecosystem.get("features"), dict) else {},
            "profile": profile if isinstance(profile, dict) else {},
            "locale": {"code": locale, "name": locale_meta["name"], "flag": locale_meta["flag"], "kind": locale_meta["kind"]},
            "supported_locales": [
                {"code": code, "name": item["name"], "flag": item["flag"], "kind": item["kind"]}
                for code, item in LOCALES.items()
            ],
        }
