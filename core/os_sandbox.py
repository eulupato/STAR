"""Sandbox operacional da STAR.

O CodeLab antigo continua útil para scripts pequenos confiáveis, mas esta camada
fornece um backend de isolamento de SO/container para código não confiável quando
Docker/Podman ou bubblewrap já estão instalados localmente.

A STAR nunca baixa imagens, instala runtimes ou habilita rede silenciosamente.
Sem backend real disponível, a execução sandboxed falha fechada.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Sequence


@dataclass(frozen=True)
class SandboxResult:
    ok: bool
    backend: str | None
    stdout: str
    stderr: str
    returncode: int | None
    timed_out: bool
    os_grade: bool
    network_enabled: bool
    reason: str | None = None


class OSSandbox:
    """Runner fail-closed usando um mecanismo de isolamento já instalado."""

    MAX_OUTPUT = 20000
    CONTAINER_IMAGE = "python:3.12-slim"

    def __init__(self, *, backend: str | None = None, image: str | None = None):
        requested = (backend or os.getenv("STAR_SANDBOX_BACKEND") or "auto").strip().lower()
        self.image = (image or os.getenv("STAR_SANDBOX_IMAGE") or self.CONTAINER_IMAGE).strip()
        self.backend = self._detect_backend(requested)

    @staticmethod
    def _detect_backend(requested: str) -> str | None:
        aliases = {"docker": "docker", "podman": "podman", "bwrap": "bwrap", "bubblewrap": "bwrap"}
        if requested not in {"", "auto"}:
            target = aliases.get(requested)
            return target if target and shutil.which(target) else None
        for candidate in ("docker", "podman", "bwrap"):
            if shutil.which(candidate):
                return candidate
        return None

    def _container_image_ready(self) -> bool:
        if self.backend not in {"docker", "podman"}:
            return False
        try:
            proc = subprocess.run(
                [self.backend, "image", "inspect", self.image],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=4,
                check=False,
            )
            return proc.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def ready(self) -> bool:
        if self.backend in {"docker", "podman"}:
            return self._container_image_ready()
        return self.backend == "bwrap" and bool(shutil.which("bwrap"))

    def _container_command(
        self,
        workspace: Path,
        argv: Sequence[str],
        *,
        network: bool,
        memory_mb: int,
        cpus: float,
    ) -> list[str]:
        command = [
            str(self.backend), "run", "--rm",
            "--read-only",
            "--pids-limit", "64",
            "--memory", f"{max(64, min(int(memory_mb), 2048))}m",
            "--cpus", str(max(0.1, min(float(cpus), 4.0))),
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
            "-v", f"{workspace}:/workspace:ro",
            "-w", "/workspace",
        ]
        command += ["--network", "bridge" if network else "none"]
        command += [self.image, *argv]
        return command

    @staticmethod
    def _bwrap_command(workspace: Path, argv: Sequence[str], *, network: bool) -> list[str]:
        command = [
            "bwrap",
            "--die-with-parent",
            "--new-session",
            "--unshare-pid",
            "--unshare-ipc",
            "--unshare-uts",
            "--proc", "/proc",
            "--dev", "/dev",
            "--tmpfs", "/tmp",
            "--ro-bind", str(workspace), "/workspace",
            "--chdir", "/workspace",
        ]
        if not network:
            command.append("--unshare-net")
        for system_path in ("/usr", "/bin", "/lib", "/lib64", "/etc"):
            if Path(system_path).exists():
                command += ["--ro-bind", system_path, system_path]
        return [*command, *argv]

    def build_command(
        self,
        workspace: Path,
        argv: Sequence[str],
        *,
        network: bool = False,
        memory_mb: int = 256,
        cpus: float = 0.5,
    ) -> list[str]:
        if self.backend in {"docker", "podman"}:
            return self._container_command(workspace, argv, network=network, memory_mb=memory_mb, cpus=cpus)
        if self.backend == "bwrap":
            return self._bwrap_command(workspace, argv, network=network)
        raise RuntimeError("nenhum backend de sandbox de SO disponível")

    def run_python(
        self,
        code: str,
        *,
        timeout: float = 5.0,
        network: bool = False,
        memory_mb: int = 256,
        cpus: float = 0.5,
    ) -> dict:
        code = str(code)
        if len(code) > 200_000:
            return asdict(SandboxResult(False, self.backend, "", "código acima do limite", None, False, False, network, "code_too_large"))
        if not self.ready():
            reason = "container_image_not_local" if self.backend in {"docker", "podman"} else "os_sandbox_unavailable"
            return asdict(SandboxResult(False, self.backend, "", "sandbox real indisponível; execução bloqueada", None, False, False, network, reason))

        try:
            with tempfile.TemporaryDirectory(prefix="star_os_sandbox_") as tmp:
                workspace = Path(tmp)
                script = workspace / "main.py"
                script.write_text(code, encoding="utf-8")
                if self.backend in {"docker", "podman"}:
                    argv = ["python", "-I", "-S", "/workspace/main.py"]
                else:
                    argv = [sys.executable, "-I", "-S", "/workspace/main.py"]
                command = self.build_command(workspace, argv, network=network, memory_mb=memory_mb, cpus=cpus)
                proc = subprocess.run(
                    command,
                    cwd=workspace,
                    env={"PATH": os.environ.get("PATH", "")},
                    text=True,
                    capture_output=True,
                    timeout=max(0.2, min(float(timeout), 60.0)),
                    check=False,
                )
                return asdict(SandboxResult(
                    proc.returncode == 0,
                    self.backend,
                    proc.stdout[-self.MAX_OUTPUT:],
                    proc.stderr[-self.MAX_OUTPUT:],
                    proc.returncode,
                    False,
                    True,
                    network,
                    None if proc.returncode == 0 else "process_failed",
                ))
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout[-self.MAX_OUTPUT:] if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr[-self.MAX_OUTPUT:] if isinstance(exc.stderr, str) else ""
            return asdict(SandboxResult(False, self.backend, stdout, stderr or "tempo limite excedido", None, True, True, network, "timeout"))
        except OSError as exc:
            return asdict(SandboxResult(False, self.backend, "", str(exc), None, False, True, network, "backend_error"))

    def stats(self) -> dict:
        return {
            "backend": self.backend,
            "ready": self.ready(),
            "os_grade": bool(self.ready()),
            "default_network": False,
            "auto_downloads": False,
            "container_image": self.image if self.backend in {"docker", "podman"} else None,
            "fail_closed": True,
        }
