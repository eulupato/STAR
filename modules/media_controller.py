"""MediaController genérico da STAR.

O backend WebView roda em processo separado para não disputar o loop Tkinter.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse
from threading import RLock, Thread

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
        self._stderr_lines = deque(maxlen=30)
        self._stderr_thread = None

    @classmethod
    def normalize_youtube_url(cls, url: str | None = None) -> str:
        value = str(url or "").strip()
        if not value:
            return "https://www.youtube.com/"

        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https":
            return "https://www.youtube.com/"

        if host in cls.ALLOWED_WEB_HOSTS:
            return value

        if host == "youtu.be":
            video_id = parsed.path.strip("/").split("/", 1)[0]
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"

        return "https://www.youtube.com/"

    def _capture_stderr(self, process: subprocess.Popen) -> None:
        stream = process.stderr
        if stream is None:
            return
        try:
            for line in stream:
                message = str(line).strip()
                if message:
                    self._stderr_lines.append(message)
        except (OSError, ValueError) as exc:
            log.debug("Leitura de stderr da STAR TV encerrada: %s", exc)

    def _start_stderr_reader(self, process: subprocess.Popen) -> None:
        self._stderr_lines.clear()
        thread = Thread(
            target=self._capture_stderr,
            args=(process,),
            daemon=True,
            name="STAR-MediaStderr",
        )
        self._stderr_thread = thread
        thread.start()

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
                target = self.normalize_youtube_url(url)
                if not self._send("load", url=target):
                    self._state.opened = False
                    return False
                self._state.opened = True
                self._state.source = "youtube"
                self._state.url = target
                self._state.last_error = None
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

            self._start_stderr_reader(self._process)
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
            process = self._process
            if process is None:
                self._state.opened = False
                self._state.fullscreen = False
                return True

            self._send("close")
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)

            thread = self._stderr_thread
            self._stderr_thread = None
            if thread is not None and thread.is_alive():
                thread.join(timeout=0.25)

            self._process = None
            self._state.opened = False
            self._state.fullscreen = False
            log.info("STAR TV fechada.")
            return True

    def state(self) -> dict:
        with self._lock:
            process = self._process
            if self._stderr_lines:
                protocol_errors = [
                    line
                    for line in self._stderr_lines
                    if line.startswith("STAR_MEDIA_ERROR:")
                ]
                if protocol_errors:
                    self._state.last_error = protocol_errors[-1][-800:]

            if process is not None and process.poll() is not None:
                self._state.opened = False
                self._state.fullscreen = False
                if self._stderr_lines:
                    self._state.last_error = "\n".join(
                        self._stderr_lines
                    )[-800:]
                self._process = None
            return asdict(self._state)
