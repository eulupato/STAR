"""MediaController genérico da STAR.

O backend WebView roda em processo separado para não disputar o loop Tkinter.
O controlador nunca bloqueia a GUI ao fechar/reiniciar a STAR TV.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
import sys
from threading import RLock, Thread
from urllib.parse import urlparse

from core.logging_config import get_logger

log = get_logger("media")

_EVENT_PREFIX = "STAR_MEDIA_EVENT:"
_ERROR_PREFIX = "STAR_MEDIA_ERROR:"


@dataclass
class MediaState:
    opened: bool = False
    starting: bool = False
    ready: bool = False
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
        self._stdout_lines = deque(maxlen=30)
        self._generation = 0

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

    @staticmethod
    def _write_command(
        process: subprocess.Popen | None,
        command: str,
        **payload,
    ) -> bool:
        if (
            process is None
            or process.poll() is not None
            or process.stdin is None
        ):
            return False
        try:
            message = json.dumps(
                {"command": command, **payload},
                ensure_ascii=False,
            )
            process.stdin.write(message + "\n")
            process.stdin.flush()
            return True
        except (OSError, BrokenPipeError, ValueError):
            return False

    def _send(self, command: str, **payload) -> bool:
        with self._lock:
            process = self._process
            ok = self._write_command(process, command, **payload)
            if not ok and process is not None:
                self._state.last_error = (
                    f"STAR TV não respondeu ao comando '{command}'."
                )
            return ok

    def _capture_stderr(
        self,
        process: subprocess.Popen,
        generation: int,
    ) -> None:
        stream = process.stderr
        if stream is None:
            return
        try:
            for line in stream:
                message = str(line).strip()
                if not message:
                    continue
                with self._lock:
                    if generation != self._generation:
                        continue
                    self._stderr_lines.append(message)
                    if message.startswith(_ERROR_PREFIX):
                        self._state.last_error = message[-800:]
        except (OSError, ValueError) as exc:
            log.debug("Leitura de stderr da STAR TV encerrada: %s", exc)

    def _capture_stdout(
        self,
        process: subprocess.Popen,
        generation: int,
    ) -> None:
        stream = process.stdout
        if stream is None:
            return
        try:
            for line in stream:
                message = str(line).strip()
                if not message:
                    continue
                with self._lock:
                    if generation != self._generation:
                        continue
                    self._stdout_lines.append(message)
                    if not message.startswith(_EVENT_PREFIX):
                        continue
                    try:
                        event = json.loads(
                            message[len(_EVENT_PREFIX):]
                        )
                    except json.JSONDecodeError:
                        continue
                    event_name = str(event.get("event") or "")
                    if event_name == "ready":
                        self._state.starting = False
                        self._state.ready = True
                        self._state.opened = True
                        self._state.last_error = None
                    elif event_name == "closing":
                        self._state.ready = False
                    elif event_name == "closed":
                        self._state.opened = False
                        self._state.starting = False
                        self._state.ready = False
                        self._state.fullscreen = False
        except (OSError, ValueError) as exc:
            log.debug("Leitura de stdout da STAR TV encerrada: %s", exc)

    def _start_readers(
        self,
        process: subprocess.Popen,
        generation: int,
    ) -> None:
        Thread(
            target=self._capture_stderr,
            args=(process, generation),
            daemon=True,
            name=f"STAR-MediaStderr-{generation}",
        ).start()
        Thread(
            target=self._capture_stdout,
            args=(process, generation),
            daemon=True,
            name=f"STAR-MediaStdout-{generation}",
        ).start()

    @staticmethod
    def _reap_process(process: subprocess.Popen) -> None:
        """Finaliza um host antigo sem bloquear o thread Tkinter."""
        try:
            process.wait(timeout=1.2)
            return
        except subprocess.TimeoutExpired:
            pass
        except (OSError, ValueError):
            return

        try:
            process.terminate()
            process.wait(timeout=0.8)
            return
        except subprocess.TimeoutExpired:
            pass
        except (OSError, ValueError):
            return

        try:
            process.kill()
            process.wait(timeout=0.8)
        except (subprocess.TimeoutExpired, OSError, ValueError):
            log.warning("STAR TV não encerrou normalmente após kill().")

    def open_youtube(
        self,
        *,
        url: str | None = None,
        rect=None,
    ) -> bool:
        target = self.normalize_youtube_url(url)

        with self._lock:
            process = self._process
            if process is not None and process.poll() is None:
                if self._write_command(process, "load", url=target):
                    self._write_command(process, "show")
                    self._state.opened = True
                    self._state.source = "youtube"
                    self._state.url = target
                    self._state.last_error = None
                    if rect:
                        self._rect = tuple(
                            int(value) for value in rect
                        )
                        self._write_command(
                            process,
                            "rect",
                            x=self._rect[0],
                            y=self._rect[1],
                            width=self._rect[2],
                            height=self._rect[3],
                        )
                    return True

                stale = process
                self._process = None
                self._generation += 1
                Thread(
                    target=self._reap_process,
                    args=(stale,),
                    daemon=True,
                    name="STAR-MediaReap-Stale",
                ).start()

            command = [
                sys.executable,
                "-m",
                "modules.media_host",
                "--url",
                target,
            ]
            if rect:
                x, y, width, height = [
                    int(value) for value in rect
                ]
                command += [
                    "--x",
                    str(x),
                    "--y",
                    str(y),
                    "--width",
                    str(width),
                    "--height",
                    str(height),
                ]
                self._rect = (x, y, width, height)

            try:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    cwd=str(
                        Path(__file__).resolve().parent.parent
                    ),
                )
            except OSError as exc:
                self._state = MediaState(last_error=str(exc))
                log.error(
                    "Não foi possível iniciar STAR TV: %s",
                    exc,
                )
                return False

            self._generation += 1
            generation = self._generation
            self._process = process
            self._stderr_lines.clear()
            self._stdout_lines.clear()
            self._state = MediaState(
                opened=True,
                starting=True,
                ready=False,
                source="youtube",
                url=target,
                fullscreen=False,
            )
            self._start_readers(process, generation)
            log.info("STAR TV iniciada em processo WebView isolado.")
            return True

    def sync_rect(self, rect) -> bool:
        if not rect:
            return False
        with self._lock:
            if (
                not self._state.opened
                or self._state.fullscreen
            ):
                return False
            x, y, width, height = [
                int(value) for value in rect
            ]
            candidate = (x, y, width, height)
            if candidate == self._rect:
                return True
            self._rect = candidate
            return self._write_command(
                self._process,
                "rect",
                x=x,
                y=y,
                width=width,
                height=height,
            )

    def play(self) -> bool:
        return self._send("play")

    def pause(self) -> bool:
        return self._send("pause")

    def volume(self, value: int) -> bool:
        level = max(0, min(100, int(value)))
        return self._send("volume", value=level)

    def fullscreen(self) -> bool:
        with self._lock:
            if not self._state.opened:
                return False
            if self._state.fullscreen:
                return True
            if self._write_command(
                self._process,
                "fullscreen",
            ):
                self._state.fullscreen = True
                return True
            return False

    def restore(self) -> bool:
        with self._lock:
            if not self._state.opened:
                return False
            if not self._state.fullscreen:
                return True
            if not self._write_command(
                self._process,
                "fullscreen",
            ):
                return False
            self._state.fullscreen = False
            rect = self._rect

        if rect:
            self.sync_rect(rect)
        return True

    def hide(self) -> bool:
        return self._send("hide")

    def show(self) -> bool:
        return self._send("show")

    def close(self, *, wait: bool = False) -> bool:
        """Fecha a TV sem travar a interface."""
        with self._lock:
            process = self._process
            if process is None:
                self._state.opened = False
                self._state.starting = False
                self._state.ready = False
                self._state.fullscreen = False
                return True

            self._write_command(process, "hide")
            self._write_command(process, "close")
            self._process = None
            self._generation += 1
            self._state.opened = False
            self._state.starting = False
            self._state.ready = False
            self._state.fullscreen = False

        worker = Thread(
            target=self._reap_process,
            args=(process,),
            daemon=not wait,
            name="STAR-MediaReap",
        )
        worker.start()
        if wait:
            worker.join(timeout=3.2)
        log.info("STAR TV solicitou encerramento.")
        return True

    def state(self) -> dict:
        with self._lock:
            process = self._process
            if process is not None and process.poll() is not None:
                return_code = process.poll()
                self._process = None
                self._state.opened = False
                self._state.starting = False
                self._state.ready = False
                self._state.fullscreen = False
                if self._stderr_lines:
                    self._state.last_error = "\n".join(
                        self._stderr_lines
                    )[-800:]
                elif return_code not in {0, None}:
                    self._state.last_error = (
                        "STAR TV encerrou inesperadamente "
                        f"(código {return_code})."
                    )
            return asdict(self._state)

    def shutdown(self) -> None:
        self.close(wait=True)
