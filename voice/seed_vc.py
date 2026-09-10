"""Integração opcional do Seed-VC com o subsistema de voz da STAR.

O código do Seed-VC não é copiado para a STAR. Ele permanece como runtime local
externo (GPLv3), instalado em ``voice/external/seed-vc`` e ignorado pelo Git.
Esta ponte usa as interfaces de linha de comando públicas do projeto.

Capacidades expostas:
- voice conversion zero-shot V1;
- singing voice conversion V1;
- voice/accent/style conversion V2;
- anonymization V2;
- conversão em tempo real;
- fine-tuning explícito V1/V2.

Nada é carregado no startup da STAR e nenhum modelo é obrigatório para o Core.
"""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = ROOT / "voice" / "output" / "seed-vc"
UPSTREAM_URL = "https://github.com/Plachtaa/seed-vc.git"
UPSTREAM_REVISION = "51383efd921027683c89e5348211d93ff12ac2a8"


def _config() -> tuple[bool, Path]:
    try:
        from config import VOICE_CONVERSION_ENABLED, VOICE_CONVERSION_HOME
    except Exception:
        VOICE_CONVERSION_ENABLED = True
        VOICE_CONVERSION_HOME = "voice/external/seed-vc"

    env_enabled = os.getenv("STAR_SEED_VC_ENABLED")
    if env_enabled is None:
        enabled = bool(VOICE_CONVERSION_ENABLED)
    else:
        enabled = env_enabled.strip().lower() in {"1", "true", "yes", "on"}

    raw_home = os.getenv("STAR_SEED_VC_HOME", str(VOICE_CONVERSION_HOME)).strip()
    home = Path(raw_home).expanduser()
    if not home.is_absolute():
        home = ROOT / home
    return enabled, home.resolve()


class SeedVCError(RuntimeError):
    """Erro de configuração ou execução do backend Seed-VC."""


class SeedVCBackend:
    """Adapter local e lazy para Seed-VC.

    A STAR continua dona da orquestração, identidade e referência de voz. O
    Seed-VC é somente um mecanismo substituível de transformação de áudio.
    """

    def __init__(self, home: Path | str | None = None):
        enabled, configured_home = _config()
        self.enabled = enabled
        self.home = Path(home).expanduser().resolve() if home else configured_home
        self.python_path = self._resolve_runtime_python()
        self.last_error: str | None = None
        self.last_output: Path | None = None
        self._realtime_process: subprocess.Popen | None = None

    def _resolve_runtime_python(self) -> Path:
        raw = os.getenv("STAR_SEED_VC_PYTHON", "").strip()
        if raw:
            return Path(raw).expanduser().resolve()
        candidates = (
            self.home / ".venv" / "Scripts" / "python.exe",
            self.home / ".venv" / "bin" / "python",
        )
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()
        return candidates[0]

    @property
    def missing_components(self) -> list[str]:
        missing: list[str] = []
        if not self.home.exists():
            missing.append(f"runtime Seed-VC ausente: {self.home}")
            return missing
        for filename in ("inference.py", "inference_v2.py", "real-time-gui.py"):
            if not (self.home / filename).exists():
                missing.append(f"arquivo Seed-VC ausente: {filename}")
        if not self.python_path.exists():
            missing.append(f"ambiente Seed-VC ausente: {self.python_path}")
        return missing

    @property
    def configured(self) -> bool:
        return self.enabled and not self.missing_components

    @property
    def status_message(self) -> str:
        if not self.enabled:
            return "desativado pela configuração"
        if self.configured:
            return "configurado"
        return "; ".join(self.missing_components)

    @property
    def capabilities(self) -> dict[str, bool]:
        home = self.home
        return {
            "voice_conversion": (home / "inference.py").exists(),
            "singing_voice_conversion": (home / "inference.py").exists(),
            "voice_accent_style_v2": (home / "inference_v2.py").exists(),
            "anonymization_v2": (home / "inference_v2.py").exists(),
            "realtime_voice_conversion": (home / "real-time-gui.py").exists(),
            "finetune_v1": (home / "train.py").exists(),
            "finetune_v2": (home / "train_v2.py").exists(),
        }

    @staticmethod
    def _bool(value: bool) -> str:
        return "true" if value else "false"

    @staticmethod
    def _require_file(path: Path | str, label: str) -> Path:
        resolved = Path(path).expanduser().resolve()
        if not resolved.is_file():
            raise SeedVCError(f"{label} não encontrado: {resolved}")
        return resolved

    def _require_ready(self) -> None:
        if not self.enabled:
            raise SeedVCError("Seed-VC está desativado pela configuração da STAR.")
        if self.missing_components:
            raise SeedVCError("Seed-VC não configurado: " + self.status_message)

    def _new_output_dir(self, purpose: str) -> Path:
        output = OUTPUT_ROOT / f"{purpose}-{uuid.uuid4().hex[:10]}"
        output.mkdir(parents=True, exist_ok=False)
        return output

    def _run(self, args: list[str], timeout: float | None = None) -> subprocess.CompletedProcess:
        self._require_ready()
        try:
            result = subprocess.run(
                [str(self.python_path), *args],
                cwd=str(self.home),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            raise SeedVCError(self.last_error) from exc

        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "erro desconhecido").strip()
            self.last_error = (
                f"Seed-VC encerrou com código {result.returncode}: {detail[-3000:]}"
            )
            raise SeedVCError(self.last_error)

        self.last_error = None
        return result

    @staticmethod
    def _find_wav(output_dir: Path) -> Path:
        files = sorted(
            output_dir.glob("*.wav"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        if not files:
            raise SeedVCError(f"Seed-VC terminou sem gerar WAV em {output_dir}")
        return files[0]

    def convert_v1(
        self,
        source: Path | str,
        target: Path | str,
        *,
        singing: bool = False,
        diffusion_steps: int = 25,
        length_adjust: float = 1.0,
        inference_cfg_rate: float = 0.7,
        auto_f0_adjust: bool = False,
        semi_tone_shift: int = 0,
        checkpoint: Path | str | None = None,
        config: Path | str | None = None,
        fp16: bool = True,
        timeout: float | None = None,
    ) -> Path:
        source_path = self._require_file(source, "Áudio de origem")
        target_path = self._require_file(target, "Referência de voz")
        output = self._new_output_dir("svc" if singing else "vc-v1")
        args = [
            "inference.py",
            "--source", str(source_path),
            "--target", str(target_path),
            "--output", str(output),
            "--diffusion-steps", str(max(1, int(diffusion_steps))),
            "--length-adjust", str(float(length_adjust)),
            "--inference-cfg-rate", str(float(inference_cfg_rate)),
            "--f0-condition", self._bool(singing),
            "--auto-f0-adjust", self._bool(auto_f0_adjust),
            "--semi-tone-shift", str(int(semi_tone_shift)),
            "--fp16", self._bool(fp16),
        ]
        if checkpoint:
            args.extend(
                ["--checkpoint", str(self._require_file(checkpoint, "Checkpoint V1"))]
            )
        if config:
            args.extend(
                ["--config", str(self._require_file(config, "Configuração V1"))]
            )
        self._run(args, timeout=timeout)
        self.last_output = self._find_wav(output)
        return self.last_output

    def convert_v2(
        self,
        source: Path | str,
        target: Path | str,
        *,
        diffusion_steps: int = 30,
        length_adjust: float = 1.0,
        intelligibility: float = 0.7,
        similarity: float = 0.7,
        convert_style: bool = False,
        anonymization_only: bool = False,
        top_p: float = 0.9,
        temperature: float = 1.0,
        repetition_penalty: float = 1.0,
        compile_model: bool = False,
        ar_checkpoint: Path | str | None = None,
        cfm_checkpoint: Path | str | None = None,
        timeout: float | None = None,
    ) -> Path:
        source_path = self._require_file(source, "Áudio de origem")
        target_path = self._require_file(target, "Referência de voz")
        output = self._new_output_dir("vc-v2")
        args = [
            "inference_v2.py",
            "--source", str(source_path),
            "--target", str(target_path),
            "--output", str(output),
            "--diffusion-steps", str(max(1, int(diffusion_steps))),
            "--length-adjust", str(float(length_adjust)),
            "--intelligibility-cfg-rate", str(float(intelligibility)),
            "--similarity-cfg-rate", str(float(similarity)),
            "--top-p", str(float(top_p)),
            "--temperature", str(float(temperature)),
            "--repetition-penalty", str(float(repetition_penalty)),
            "--convert-style", self._bool(convert_style),
            "--anonymization-only", self._bool(anonymization_only),
        ]
        # O upstream usa argparse(type=bool): passar "false" resultaria em True.
        if compile_model:
            args.extend(["--compile", "True"])
        if ar_checkpoint:
            args.extend(
                [
                    "--ar-checkpoint-path",
                    str(self._require_file(ar_checkpoint, "Checkpoint AR V2")),
                ]
            )
        if cfm_checkpoint:
            args.extend(
                [
                    "--cfm-checkpoint-path",
                    str(self._require_file(cfm_checkpoint, "Checkpoint CFM V2")),
                ]
            )
        self._run(args, timeout=timeout)
        self.last_output = self._find_wav(output)
        return self.last_output

    def launch_realtime(
        self,
        *,
        checkpoint: Path | str | None = None,
        config: Path | str | None = None,
        fp16: bool = True,
        gpu: int = 0,
    ) -> subprocess.Popen:
        self._require_ready()
        if self._realtime_process is not None and self._realtime_process.poll() is None:
            return self._realtime_process

        args = [
            str(self.python_path),
            "real-time-gui.py",
            "--fp16", self._bool(fp16),
            "--gpu", str(max(0, int(gpu))),
        ]
        if checkpoint:
            args.extend(
                [
                    "--checkpoint-path",
                    str(self._require_file(checkpoint, "Checkpoint realtime")),
                ]
            )
        if config:
            args.extend(
                [
                    "--config-path",
                    str(self._require_file(config, "Configuração realtime")),
                ]
            )
        self._realtime_process = subprocess.Popen(args, cwd=str(self.home))
        return self._realtime_process

    def stop_realtime(self) -> None:
        process = self._realtime_process
        self._realtime_process = None
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            process.kill()

    def start_finetune_v1(
        self,
        dataset_dir: Path | str,
        *,
        run_name: str = "star_voice",
        config: str = "./configs/presets/config_dit_mel_seed_uvit_xlsr_tiny.yml",
        pretrained_checkpoint: Path | str | None = None,
        batch_size: int = 2,
        max_steps: int = 1000,
        max_epochs: int = 1000,
        save_every: int = 500,
        num_workers: int = 0,
        gpu: int = 0,
    ) -> subprocess.Popen:
        self._require_ready()
        dataset = Path(dataset_dir).expanduser().resolve()
        if not dataset.is_dir():
            raise SeedVCError(f"Dataset não encontrado: {dataset}")
        args = [
            str(self.python_path), "train.py",
            "--config", config,
            "--dataset-dir", str(dataset),
            "--run-name", str(run_name),
            "--batch-size", str(max(1, int(batch_size))),
            "--max-steps", str(max(1, int(max_steps))),
            "--max-epochs", str(max(1, int(max_epochs))),
            "--save-every", str(max(1, int(save_every))),
            "--num-workers", str(max(0, int(num_workers))),
            "--gpu", str(max(0, int(gpu))),
        ]
        if pretrained_checkpoint:
            args.extend(
                [
                    "--pretrained-ckpt",
                    str(self._require_file(pretrained_checkpoint, "Checkpoint pré-treinado")),
                ]
            )
        return subprocess.Popen(args, cwd=str(self.home))

    def start_finetune_v2(
        self,
        dataset_dir: Path | str,
        *,
        run_name: str = "star_voice_v2",
        config: str = "configs/v2/vc_wrapper.yaml",
        pretrained_cfm: Path | str | None = None,
        pretrained_ar: Path | str | None = None,
        train_cfm: bool = True,
        train_ar: bool = True,
        batch_size: int = 2,
        max_steps: int = 1000,
        max_epochs: int = 1000,
        save_every: int = 500,
        num_workers: int = 0,
    ) -> subprocess.Popen:
        self._require_ready()
        if not train_cfm and not train_ar:
            raise SeedVCError("Fine-tuning V2 precisa treinar CFM, AR ou ambos.")
        dataset = Path(dataset_dir).expanduser().resolve()
        if not dataset.is_dir():
            raise SeedVCError(f"Dataset não encontrado: {dataset}")
        args = [
            str(self.python_path), "train_v2.py",
            "--config", config,
            "--dataset-dir", str(dataset),
            "--run-name", str(run_name),
            "--batch-size", str(max(1, int(batch_size))),
            "--max-steps", str(max(1, int(max_steps))),
            "--max-epochs", str(max(1, int(max_epochs))),
            "--save-every", str(max(1, int(save_every))),
            "--num-workers", str(max(0, int(num_workers))),
        ]
        if train_cfm:
            args.append("--train-cfm")
        if train_ar:
            args.append("--train-ar")
        if pretrained_cfm:
            args.extend(
                [
                    "--pretrained-cfm-ckpt",
                    str(self._require_file(pretrained_cfm, "Checkpoint CFM pré-treinado")),
                ]
            )
        if pretrained_ar:
            args.extend(
                [
                    "--pretrained-ar-ckpt",
                    str(self._require_file(pretrained_ar, "Checkpoint AR pré-treinado")),
                ]
            )
        return subprocess.Popen(args, cwd=str(self.home))

    @staticmethod
    def _bootstrap_command() -> list[str]:
        raw = os.getenv("STAR_SEED_VC_BOOTSTRAP_PYTHON", "").strip()
        if raw:
            return shlex.split(raw)
        candidates: list[list[str]] = []
        if os.name == "nt" and shutil.which("py"):
            candidates.append(["py", "-3.10"])
        if shutil.which("python3.10"):
            candidates.append(["python3.10"])
        candidates.append([sys.executable])
        for command in candidates:
            try:
                probe = subprocess.run(
                    [*command, "--version"],
                    capture_output=True,
                    timeout=5,
                )
                if probe.returncode == 0:
                    return command
            except Exception:
                continue
        return [sys.executable]

    def install(self, *, upgrade_pip: bool = True) -> None:
        """Instala o runtime externo local sem adicionar seus arquivos ao Git."""
        if not shutil.which("git"):
            raise SeedVCError("Git não foi encontrado no sistema.")

        self.home.parent.mkdir(parents=True, exist_ok=True)
        if not self.home.exists():
            subprocess.run(
                ["git", "clone", "--depth", "1", UPSTREAM_URL, str(self.home)],
                check=True,
            )
        elif not (self.home / ".git").exists():
            raise SeedVCError(
                f"Diretório existe, mas não é um clone Seed-VC: {self.home}"
            )

        revision = os.getenv("STAR_SEED_VC_REVISION", UPSTREAM_REVISION).strip()
        checkout = subprocess.run(
            ["git", "-C", str(self.home), "checkout", revision],
            capture_output=True,
            text=True,
        )
        if checkout.returncode != 0:
            subprocess.run(
                [
                    "git", "-C", str(self.home), "fetch", "origin", revision,
                    "--depth", "1",
                ],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(self.home), "checkout", revision],
                check=True,
            )

        runtime_python = self.home / ".venv" / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        if not runtime_python.exists():
            subprocess.run(
                [*self._bootstrap_command(), "-m", "venv", str(self.home / ".venv")],
                check=True,
            )

        self.python_path = runtime_python.resolve()
        if upgrade_pip:
            subprocess.run(
                [str(self.python_path), "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
            )
        subprocess.run(
            [
                str(self.python_path), "-m", "pip", "install", "-r",
                str(self.home / "requirements.txt"),
            ],
            cwd=str(self.home),
            check=True,
        )

    def close(self) -> None:
        self.stop_realtime()


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="STAR Seed-VC backend")
    parser.add_argument("command", choices=("status", "install"))
    args = parser.parse_args(argv)

    backend = SeedVCBackend()
    if args.command == "install":
        backend.install()
        print("✅ Seed-VC instalado como runtime local opcional da STAR.")
        return 0

    print(f"Seed-VC: {backend.status_message}")
    print(f"Runtime: {backend.home}")
    print(f"Python: {backend.python_path}")
    for name, available in backend.capabilities.items():
        print(f"- {name}: {'sim' if available else 'não'}")
    return 0 if backend.configured else 1


if __name__ == "__main__":
    raise SystemExit(main())