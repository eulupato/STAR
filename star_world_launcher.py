"""Launcher oficial do STAR WORLD 3D.

A engine 3D é apenas uma superfície. O mesmo STAR Core Python continua sendo a
fonte de identidade, memória, cognição, voz, ferramentas e permissões.
"""
from __future__ import annotations

import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time

from core.release import VERSION
from main import (
    _configure_console_io,
    _print_runtime_summary,
    _start_device_gateway,
    create_star,
)


ROOT = Path(__file__).resolve().parent
WORLD_DIR = ROOT / "star_world"


def _env_flag(name: str) -> bool:
    return str(os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def _godot_candidates():
    explicit = str(os.getenv("STAR_GODOT_EXE") or "").strip()
    if explicit:
        yield Path(explicit)

    located = shutil.which("godot") or shutil.which("godot4")
    if located:
        yield Path(located)

    local = Path(os.getenv("LOCALAPPDATA") or "")
    packages = local / "Microsoft" / "WinGet" / "Packages"
    if packages.exists():
        for package in sorted(packages.glob("GodotEngine.GodotEngine_*")):
            for executable in sorted(
                package.glob("Godot_v*-stable_win64.exe"),
                reverse=True,
            ):
                yield executable


def find_godot() -> Path | None:
    seen: set[str] = set()
    for candidate in _godot_candidates():
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        key = str(resolved).casefold()
        if key in seen:
            continue
        seen.add(key)
        if resolved.is_file():
            return resolved
    return None


def _run_classic_fallback(reason: str) -> int:
    print(f"⚠️ {reason}")
    print("↩️ Iniciando a interface clássica da STAR como fallback.")
    from main import run_surface

    return run_surface("pc")


def _start_core(result_queue: queue.Queue) -> None:
    try:
        result_queue.put(("ready", create_star()))
    except Exception as exc:
        result_queue.put(("error", exc))


def run_star_world() -> int:
    _configure_console_io()

    if _env_flag("STAR_PC_CLASSIC"):
        return _run_classic_fallback("Modo clássico solicitado por STAR_PC_CLASSIC.")

    godot = find_godot()
    if godot is None:
        return _run_classic_fallback("Godot não encontrado.")

    project_file = WORLD_DIR / "project.godot"
    if not project_file.exists():
        return _run_classic_fallback("STAR WORLD 3D não está instalado.")

    print("=" * 60)
    print(f"⭐ STAR V{VERSION} — STAR WORLD 3D")
    print("=" * 60)
    print(f"🎮 Godot: {godot}")

    # O Gateway precisa existir no processo Python, não apenas no ambiente
    # entregue ao Godot. O cliente 3D conecta exclusivamente pelo loopback.
    os.environ.setdefault("STAR_DEVICE_GATEWAY", "1")

    env = os.environ.copy()
    env["STAR_ROOT"] = str(ROOT)
    env["STAR_WORLD"] = "1"
    env["STAR_DEVICE_GATEWAY"] = "1"
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    core_result: queue.Queue = queue.Queue(maxsize=1)
    threading.Thread(
        target=_start_core,
        args=(core_result,),
        daemon=True,
        name="STAR-World-CoreStartup",
    ).start()

    try:
        process = subprocess.Popen(
            [str(godot), "--path", str(WORLD_DIR)],
            cwd=str(WORLD_DIR),
            env=env,
        )
    except OSError as exc:
        return _run_classic_fallback(
            f"Godot foi encontrado, mas não pôde ser iniciado: {exc}"
        )

    star = None
    gateway = None
    core_finished = False

    try:
        while process.poll() is None:
            if not core_finished:
                try:
                    kind, payload = core_result.get_nowait()
                except queue.Empty:
                    pass
                else:
                    core_finished = True
                    if kind == "ready":
                        star = payload
                        gateway = _start_device_gateway(star)
                        if gateway is None:
                            print("⚠️ STAR Device Gateway não iniciou; chat e estado 3D ficarão indisponíveis.")
                        else:
                            star.proactivity.start()
                            threading.Thread(
                                target=_print_runtime_summary,
                                args=(star,),
                                daemon=True,
                                name="STAR-World-StartupSummary",
                            ).start()
                            print("✅ STAR Core conectado ao STAR WORLD.")
                    else:
                        print(
                            "❌ STAR Core não iniciou: "
                            f"{type(payload).__name__}: {payload}"
                        )
            time.sleep(0.10)
    except KeyboardInterrupt:
        if process.poll() is None:
            process.terminate()
    finally:
        if star is not None:
            try:
                star.proactivity.stop()
            except Exception:
                pass
        if gateway is not None:
            try:
                gateway.stop()
            except Exception:
                pass
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=3)
            except Exception:
                process.kill()
                process.wait(timeout=3)

    return int(process.returncode or 0)


if __name__ == "__main__":
    raise SystemExit(run_star_world())
