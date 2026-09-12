"""Clima contextual da STAR.

A capacidade é online, sob demanda e compatível com o princípio local-first:
nenhuma consulta ocorre em background. Quando uma conversa ou comando realmente
depende do clima, a STAR consulta Open-Meteo. Se nenhuma localização padrão foi
configurada, ela pode estimar cidade/região pela conexão de internet sem persistir
coordenadas em disco.

Variáveis de ambiente:
- STAR_WEATHER_ENABLED=0 desativa a capacidade.
- STAR_WEATHER_LOCATION="Cidade, Estado" fixa a localização preferida.
- STAR_WEATHER_AUTOLOCATE=0 desativa estimativa por IP.
- STAR_WEATHER_CACHE_SECONDS=600 controla o cache em memória.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


USER_AGENT = "STAR/1.9 weather-context"
OPEN_METEO_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
IP_LOCATION = "https://ipwho.is/"


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "sim"}


@dataclass(frozen=True)
class WeatherSnapshot:
    location: str
    temperature_c: float
    feels_like_c: float
    humidity_pct: int
    precipitation_mm: float
    rain_mm: float
    cloud_cover_pct: int
    weather_code: int
    wind_kmh: float
    is_day: bool
    observed_at: str
    source: str = "Open-Meteo"

    @property
    def rainy(self) -> bool:
        return (
            self.precipitation_mm > 0
            or self.rain_mm > 0
            or self.weather_code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
        )

    @property
    def snowy(self) -> bool:
        return self.weather_code in {71, 73, 75, 77, 85, 86}

    @property
    def stormy(self) -> bool:
        return self.weather_code in {95, 96, 99}

    @property
    def clear_or_partly_cloudy(self) -> bool:
        return self.weather_code in {0, 1, 2} and not self.rainy

    @property
    def temperature_band(self) -> str:
        temp = self.temperature_c
        if temp >= 32:
            return "muito_quente"
        if temp >= 26:
            return "quente"
        if temp >= 19:
            return "ameno"
        if temp >= 13:
            return "fresco"
        if temp >= 7:
            return "frio"
        return "muito_frio"


WEATHER_DESCRIPTIONS = {
    0: "céu limpo",
    1: "predominantemente limpo",
    2: "parcialmente nublado",
    3: "nublado",
    45: "neblina",
    48: "neblina com geada",
    51: "garoa fraca",
    53: "garoa moderada",
    55: "garoa forte",
    56: "garoa congelante fraca",
    57: "garoa congelante forte",
    61: "chuva fraca",
    63: "chuva moderada",
    65: "chuva forte",
    66: "chuva congelante fraca",
    67: "chuva congelante forte",
    71: "neve fraca",
    73: "neve moderada",
    75: "neve forte",
    77: "grãos de neve",
    80: "pancadas de chuva fracas",
    81: "pancadas de chuva moderadas",
    82: "pancadas de chuva fortes",
    85: "pancadas de neve fracas",
    86: "pancadas de neve fortes",
    95: "trovoadas",
    96: "trovoadas com granizo",
    99: "trovoadas fortes com granizo",
}


def weather_description(code: int) -> str:
    return WEATHER_DESCRIPTIONS.get(int(code), "condição variável")


class WeatherService:
    """Provider pequeno, cacheado e sem dependências externas."""

    def __init__(
        self,
        *,
        enabled: bool | None = None,
        default_location: str | None = None,
        auto_locate: bool | None = None,
        cache_seconds: int | None = None,
        timeout: float = 5.0,
    ):
        self.enabled = _env_flag("STAR_WEATHER_ENABLED", True) if enabled is None else bool(enabled)
        configured_location = default_location if default_location is not None else os.getenv("STAR_WEATHER_LOCATION", "")
        self.default_location = str(configured_location or "").strip()
        self.auto_locate = _env_flag("STAR_WEATHER_AUTOLOCATE", True) if auto_locate is None else bool(auto_locate)
        raw_cache = os.getenv("STAR_WEATHER_CACHE_SECONDS", "600")
        self.cache_seconds = max(60, int(cache_seconds if cache_seconds is not None else raw_cache))
        self.timeout = max(1.0, float(timeout))
        self._cache: dict[str, tuple[float, WeatherSnapshot]] = {}
        self.last_error: str | None = None

    def current(self, location: str | None = None) -> WeatherSnapshot | None:
        if not self.enabled:
            self.last_error = "clima desativado"
            return None

        requested = str(location or self.default_location or "").strip()
        cache_key = requested.casefold() or "__auto__"
        cached = self._cache.get(cache_key)
        if cached and (time.monotonic() - cached[0]) <= self.cache_seconds:
            return cached[1]

        try:
            if requested:
                lat, lon, label = self._geocode(requested)
            elif self.auto_locate:
                lat, lon, label = self._autolocate()
            else:
                self.last_error = "localização não configurada"
                return None
            snapshot = self._forecast(lat, lon, label)
            self._cache[cache_key] = (time.monotonic(), snapshot)
            self.last_error = None
            return snapshot
        except (OSError, TimeoutError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            self.last_error = str(exc)
            return None

    def _json(self, url: str) -> dict[str, Any]:
        req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("resposta meteorológica inválida")
        return data

    def _geocode(self, location: str) -> tuple[float, float, str]:
        cleaned = " ".join(str(location).strip().split())
        if not cleaned or len(cleaned) > 100:
            raise ValueError("localização inválida")
        params = urlencode({"name": cleaned, "count": 1, "language": "pt", "format": "json"})
        data = self._json(f"{OPEN_METEO_GEOCODING}?{params}")
        results = data.get("results") or []
        if not results:
            raise ValueError(f"não encontrei a localização '{cleaned}'")
        item = results[0]
        label_parts = [item.get("name"), item.get("admin1"), item.get("country")]
        label = ", ".join(str(part) for part in label_parts if part)
        return float(item["latitude"]), float(item["longitude"]), label or cleaned

    def _autolocate(self) -> tuple[float, float, str]:
        data = self._json(IP_LOCATION)
        if data.get("success") is False:
            raise ValueError(str(data.get("message") or "não foi possível estimar a localização"))
        lat = float(data["latitude"])
        lon = float(data["longitude"])
        label_parts = [data.get("city"), data.get("region"), data.get("country")]
        label = ", ".join(str(part) for part in label_parts if part) or "sua região"
        return lat, lon, label

    def _forecast(self, latitude: float, longitude: float, label: str) -> WeatherSnapshot:
        current_fields = ",".join(
            (
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "precipitation",
                "rain",
                "weather_code",
                "cloud_cover",
                "wind_speed_10m",
                "is_day",
            )
        )
        params = urlencode(
            {
                "latitude": f"{latitude:.6f}",
                "longitude": f"{longitude:.6f}",
                "current": current_fields,
                "timezone": "auto",
                "forecast_days": 1,
            }
        )
        data = self._json(f"{OPEN_METEO_FORECAST}?{params}")
        current = data.get("current") or {}
        return WeatherSnapshot(
            location=label,
            temperature_c=float(current["temperature_2m"]),
            feels_like_c=float(current.get("apparent_temperature", current["temperature_2m"])),
            humidity_pct=int(round(float(current.get("relative_humidity_2m", 0)))),
            precipitation_mm=float(current.get("precipitation", 0.0)),
            rain_mm=float(current.get("rain", 0.0)),
            cloud_cover_pct=int(round(float(current.get("cloud_cover", 0)))),
            weather_code=int(current.get("weather_code", -1)),
            wind_kmh=float(current.get("wind_speed_10m", 0.0)),
            is_day=bool(int(current.get("is_day", 1))),
            observed_at=str(current.get("time", "")),
        )


def format_weather(snapshot: WeatherSnapshot) -> str:
    condition = weather_description(snapshot.weather_code)
    return (
        f"Agora em {snapshot.location}: {snapshot.temperature_c:.0f} °C, "
        f"sensação de {snapshot.feels_like_c:.0f} °C e {condition}. "
        f"Umidade {snapshot.humidity_pct}% e vento de {snapshot.wind_kmh:.0f} km/h."
    )
