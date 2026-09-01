"""MediaController genérico da STAR.

O backend WebView roda em processo separado para não disputar o loop Tkinter.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
import sys
from threading import RLock

from core.logging_config import get_logger

log = get_logger("media")


@dataclass
class MediaState:
    opened: bool = False
    source: str | None = None
    url: str | None = None
    fullscreen: bool = False
    last_error: str | None = None


class MediaController:
    ALLOWED_WEB_HOSTS = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtube-nocookie.com",
        "www.youtube-nocookie.com",
    }

    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._state = MediaState()
        self._lock = RLock()
        self._rect = None

    @staticmethod
    def normalize_youtube_url(url: str | None = None) -> str:
        value = str(url or "").strip()
        if not value:
            return "https://www.youtube.com/"
        if value.startswith("https://www.youtube.com/") or value.startswith("https://m.youtube.com/"):
            return value
        if value.startswith("https://youtu.be/"):
            video_id = value.rsplit("/", 1)[-1].split("?", 1)[0]
            return f"https://www.youtube.com/watch?v={video_id}"
        return "https://www.youtube.com/"

    def _send(self, command: str, **payload) -> bool:
        with self._lock:
            process = self._process
            if process is None or process.poll() is not None or process.stdin is None:
                return False
            try:
                message = json.dumps({"command": command, **payload}, ensure_ascii=False)
                process.stdin.write(message + "\n")
                process.stdin.flush()
                return True
            except (OSError, BrokenPipeError) as exc:
                self._state.last_error = str(exc)
                log.error("Falha ao enviar comando ao media host: %s", exc)
                return False

    def open_youtube(self, *, url: str | None = None, rect=None) -> bool:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                self._state.opened = True
                self._state.source = "youtube"
                self._state.url = self.normalize_youtube_url(url)
                self._send("load", url=self._state.url)
                if rect:
                    self.sync_rect(rect)
                return True

            target = self.normalize_youtube_url(url)
            command = [
                sys.executable,
                "-m",
                "modules.media_host",
                "--url",
                target,
            ]
            if rect:
                x, y, width, height = [int(value) for value in rect]
                command += [
                    "--x", str(x),
                    "--y", str(y),
                    "--width", str(width),
                    "--height", str(height),
                ]

            try:
                self._process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    cwd=str(Path(__file__).resolve().parent.parent),
                )
            except OSError as exc:
                self._state = MediaState(last_error=str(exc))
                log.error("Não foi possível iniciar STAR TV: %s", exc)
                return False

            self._rect = rect
            self._state = MediaState(
                opened=True,
                source="youtube",
                url=target,
                fullscreen=False,
            )
            log.info("STAR TV aberta com WebView.")
            return True

    def sync_rect(self, rect) -> bool:
        if not rect or self._state.fullscreen:
            return False
        x, y, width, height = [int(value) for value in rect]
        self._rect = (x, y, width, height)
        return self._send("rect", x=x, y=y, width=width, height=height)

    def play(self) -> bool:
        return self._send("play")

    def pause(self) -> bool:
        return self._send("pause")

    def volume(self, value: int) -> bool:
        level = max(0, min(100, int(value)))
        return self._send("volume", value=level)

    def fullscreen(self) -> bool:
        if not self._state.opened:
            return False
        if not self._state.fullscreen:
            if self._send("fullscreen"):
                self._state.fullscreen = True
                return True
        return False

    def restore(self) -> bool:
        if not self._state.opened:
            return False
        if self._state.fullscreen:
            if self._send("fullscreen"):
                self._state.fullscreen = False
                if self._rect:
                    self.sync_rect(self._rect)
                return True
        return True

    def close(self) -> bool:
        with self._lock:
            if self._process is None:
                self._state.opened = False
                return True
            self._send("close")
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.terminate()
            self._process = None
            self._state.opened = False
            self._state.fullscreen = False
            log.info("STAR TV fechada.")
            return True

    def state(self) -> dict:
        with self._lock:
            if self._process is not None and self._process.poll() is not None:
                self._state.opened = False
                if self._process.stderr:
                    try:
                        error = self._process.stderr.read().strip()
                    except OSError:
                        error = ""
                    if error:
                        self._state.last_error = error[-800:]
            return asdict(self._state)
