"""Estado global compartilhado do STAR WORLD.

Mantém tempo, fuso e cenário fora da engine 3D para que Hub, Casa e demais
superfícies observem a mesma fonte de verdade. Preferências continuam em
user_settings.json, que é local e não versionado.
"""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import threading
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "user_settings.json"
DEFAULT_SCENARIO = "cosmic_crystal"
DEFAULT_SKIN = "cypher_system"
VALID_SKINS = {"casual", "cypher_system", "rock_simple", "brazil", "elegant_blue", "rich_red"}
LEGACY_SKIN_ALIASES = {
    "base.jpeg": "casual",
    "casual1.jpeg": "casual",
    "system.jpeg": "cypher_system",
    "brazil.jpeg": "brazil",
    "dress1.jpeg": "elegant_blue",
    "redpaty.jpeg": "rich_red",
    "legofshopping.jpeg": "rock_simple",
    "yk2.jpeg": "rock_simple",
}


def _read_settings(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_settings(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def _phase_for_hour(hour: int) -> str:
    hour = int(hour) % 24
    if 5 <= hour < 8:
        return "dawn"
    if 8 <= hour < 17:
        return "day"
    if 17 <= hour < 20:
        return "sunset"
    return "night"


class WorldStateService:
    """Fonte única de tempo/cenário para as superfícies do STAR WORLD."""

    def __init__(self, settings_path: Path | None = None):
        self.settings_path = Path(settings_path or DEFAULT_SETTINGS_PATH)
        self._lock = threading.RLock()

    def _timezone(self, timezone_id: str):
        timezone_id = str(timezone_id or "local").strip() or "local"
        if timezone_id == "local":
            return datetime.now().astimezone().tzinfo
        try:
            return ZoneInfo(timezone_id)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Fuso horário IANA inválido: {timezone_id}") from exc

    def settings(self) -> dict:
        with self._lock:
            data = _read_settings(self.settings_path)
        raw_skin = str(data.get("world_skin") or data.get("skin") or DEFAULT_SKIN).strip()
        skin = LEGACY_SKIN_ALIASES.get(raw_skin.casefold(), raw_skin)
        if skin not in VALID_SKINS:
            skin = DEFAULT_SKIN
        return {
            "timezone": str(data.get("timezone") or "local"),
            "world_scenario": str(data.get("world_scenario") or DEFAULT_SCENARIO),
            "world_auto_time": bool(data.get("world_auto_time", True)),
            "skin": skin,
        }

    def set_timezone(self, timezone_id: str) -> dict:
        timezone_id = str(timezone_id or "").strip()
        if not timezone_id:
            raise ValueError("Fuso horário vazio.")
        self._timezone(timezone_id)
        with self._lock:
            data = _read_settings(self.settings_path)
            data["timezone"] = timezone_id
            _write_settings(self.settings_path, data)
        return self.snapshot()

    def set_scenario(self, scenario_id: str) -> dict:
        scenario_id = str(scenario_id or "").strip()
        if not scenario_id:
            raise ValueError("Cenário vazio.")
        if len(scenario_id) > 80:
            raise ValueError("Identificador de cenário longo demais.")
        with self._lock:
            data = _read_settings(self.settings_path)
            data["world_scenario"] = scenario_id
            _write_settings(self.settings_path, data)
        return self.snapshot()

    def set_skin(self, skin_id: str) -> dict:
        skin_id = str(skin_id or "").strip()
        if skin_id not in VALID_SKINS:
            raise ValueError(f"Skin 3D inválida: {skin_id}")
        with self._lock:
            data = _read_settings(self.settings_path)
            data["world_skin"] = skin_id
            _write_settings(self.settings_path, data)
        return self.snapshot()

    def snapshot(self, now: datetime | None = None, *, online: bool = False) -> dict:
        cfg = self.settings()
        tz = self._timezone(cfg["timezone"])
        current = now.astimezone(tz) if now is not None else datetime.now(tz)
        return {
            "timezone": cfg["timezone"],
            "datetime": current.isoformat(),
            "local_date": current.date().isoformat(),
            "local_time": current.strftime("%H:%M:%S"),
            "hour": current.hour,
            "minute": current.minute,
            "day_phase": _phase_for_hour(current.hour),
            "scenario": cfg["world_scenario"],
            "skin": cfg["skin"],
            "auto_time": cfg["world_auto_time"],
            "online_sync": bool(online),
        }
