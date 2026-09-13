"""CURA — saúde, snapshots e autocorreção local controlada.

A CURA consegue reparar corrupção verificável sem GitHub/IA usando um snapshot local
conhecido como bom. Ela NÃO gera código novo, não restaura mudanças saudáveis só por
serem diferentes e não toca em segredos/runtime fora da allowlist de projeto.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import threading
import time

from sqlalchemy import text

from database.database import DATABASE_PATH, engine

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME = ROOT / "runtime" / "cure"


@dataclass
class CureReport:
    problem: str
    proposal: str
    validated: bool = False
    applied: bool = False
    tests_passed: bool = False
    notes: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class CureSystem:
    """Supervisor de saúde local, seguro e independente da nuvem."""

    SOURCE_PATTERNS = (
        "main.py", "config.py", "config_skin.json", "STAR*_MANIFEST.json",
        "core/**/*.py", "database/**/*.py", "gui/**/*.py", "modules/**/*.py",
        "voice/**/*.py", "tests/**/*.py", "clients/**/*.py", "clients/**/*.java",
        "clients/**/*.kt", "clients/**/*.swift", "clients/**/*.xml",
        "knowledge/**/manifest.json",
    )
    EXCLUDED_PARTS = {".git", ".venv", "__pycache__", "runtime", "node_modules", ".idea", ".vscode"}

    def __init__(self, root: Path | str = ROOT, *, guardian=None, runtime_dir: Path | str = DEFAULT_RUNTIME):
        self.root = Path(root).resolve()
        self.guardian = guardian
        self.runtime_dir = Path(runtime_dir)
        self.snapshots_dir = self.runtime_dir / "snapshots"
        self.pointer_path = self.runtime_dir / "known_good.json"
        self.events_path = self.runtime_dir / "events.jsonl"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        if self.guardian is not None:
            try:
                from core.guardian import ActionPolicy
                self.guardian.register_policy(ActionPolicy(
                    "cure.restore", "high", False, False, False,
                    "Restauração local de arquivo a partir de snapshot conhecido como bom",
                ))
            except Exception:
                pass

    def _event(self, kind: str, details=None):
        payload = {"timestamp": _now(), "kind": str(kind), "details": details or {}}
        try:
            self.events_path.parent.mkdir(parents=True, exist_ok=True)
            with self.events_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str) + "\n")
        except OSError:
            pass

    def _source_files(self) -> list[Path]:
        found = set()
        for pattern in self.SOURCE_PATTERNS:
            for path in self.root.glob(pattern):
                if not path.is_file():
                    continue
                try:
                    relative = path.relative_to(self.root)
                except ValueError:
                    continue
                if any(part in self.EXCLUDED_PARTS for part in relative.parts):
                    continue
                found.add(path)
        return sorted(found, key=lambda item: item.as_posix())

    def diagnose(self, problem):
        return CureReport(
            problem=str(problem),
            proposal="Executar health check local, comparar com snapshot conhecido como bom e reparar somente corrupção comprovada.",
        )

    def health_check(self, *, deep: bool = False) -> dict:
        failures = []
        warnings = []
        checked_python = checked_json = 0
        critical = [self.root / "main.py", self.root / "config.py", self.root / "STAR_MANIFEST.json"]
        for path in critical:
            if not path.is_file():
                failures.append({"kind": "missing_critical", "path": str(path.relative_to(self.root))})

        files = self._source_files()
        for path in files:
            suffix = path.suffix.casefold()
            relative = str(path.relative_to(self.root))
            if suffix == ".py":
                if not deep and path.name not in {"main.py", "config.py", "star_core.py", "executive.py", "cure.py"}:
                    continue
                checked_python += 1
                try:
                    source = path.read_text(encoding="utf-8")
                    compile(source, relative, "exec", dont_inherit=True)
                except Exception as exc:
                    failures.append({"kind": "python_syntax", "path": relative, "error": f"{type(exc).__name__}: {exc}"})
            elif suffix == ".json":
                checked_json += 1
                try:
                    json.loads(path.read_text(encoding="utf-8"))
                except Exception as exc:
                    failures.append({"kind": "json_invalid", "path": relative, "error": f"{type(exc).__name__}: {exc}"})

        db_status = "absent"
        if DATABASE_PATH.is_file():
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("PRAGMA quick_check")).scalar_one()
                db_status = str(result)
                if str(result).casefold() != "ok":
                    failures.append({"kind": "database_integrity", "path": str(DATABASE_PATH), "error": str(result)})
            except Exception as exc:
                db_status = "error"
                failures.append({"kind": "database_integrity", "path": str(DATABASE_PATH), "error": f"{type(exc).__name__}: {exc}"})

        try:
            usage = shutil.disk_usage(self.root)
            free_ratio = usage.free / max(1, usage.total)
            if free_ratio < 0.03:
                warnings.append({"kind": "low_disk", "free_bytes": usage.free, "free_ratio": free_ratio})
        except OSError:
            pass

        result = {
            "healthy": not failures,
            "deep": bool(deep),
            "failures": failures,
            "warnings": warnings,
            "python_checked": checked_python,
            "json_checked": checked_json,
            "database": db_status,
            "timestamp": _now(),
        }
        self._event("health_check", {"healthy": result["healthy"], "failures": failures, "warnings": warnings})
        return result

    def snapshot(self, label: str = "manual", *, include_database: bool = True) -> dict:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        snapshot_id = f"{stamp}-{hashlib.sha1(str(label).encode()).hexdigest()[:8]}"
        target = self.snapshots_dir / snapshot_id
        files_root = target / "files"
        files_root.mkdir(parents=True, exist_ok=False)
        manifest = {}
        for source in self._source_files():
            relative = source.relative_to(self.root)
            destination = files_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            manifest[relative.as_posix()] = _hash(source)

        database_backup = None
        if include_database and DATABASE_PATH.is_file():
            database_backup = target / "star.db"
            try:
                source_db = sqlite3.connect(str(DATABASE_PATH))
                backup_db = sqlite3.connect(str(database_backup))
                with backup_db:
                    source_db.backup(backup_db)
                backup_db.close(); source_db.close()
            except sqlite3.Error:
                database_backup = None

        meta = {
            "snapshot_id": snapshot_id,
            "label": str(label),
            "created_at": _now(),
            "files": manifest,
            "database_backup": str(database_backup) if database_backup else None,
        }
        (target / "manifest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self._event("snapshot", {"snapshot_id": snapshot_id, "label": label, "files": len(manifest)})
        return meta

    def _snapshot_meta(self, snapshot_id: str) -> dict:
        path = self.snapshots_dir / str(snapshot_id) / "manifest.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def mark_known_good(self, label: str = "known-good") -> dict:
        health = self.health_check(deep=True)
        if not health["healthy"]:
            raise RuntimeError("A versão atual falhou no health check; não pode virar snapshot conhecido como bom.")
        snap = self.snapshot(label, include_database=True)
        pointer = {"snapshot_id": snap["snapshot_id"], "accepted_at": _now(), "root": str(self.root)}
        self.pointer_path.write_text(json.dumps(pointer, ensure_ascii=False, indent=2), encoding="utf-8")
        self._event("known_good", pointer)
        return {**pointer, "health": health}

    def known_good(self) -> dict | None:
        try:
            pointer = json.loads(self.pointer_path.read_text(encoding="utf-8"))
            meta = self._snapshot_meta(pointer["snapshot_id"])
            return {**pointer, "manifest": meta}
        except (OSError, KeyError, json.JSONDecodeError):
            return None

    def ensure_known_good(self) -> dict:
        known = self.known_good()
        if known is not None:
            return {"created": False, "snapshot_id": known["snapshot_id"]}
        health = self.health_check(deep=True)
        if not health["healthy"]:
            return {"created": False, "reason": "current_state_not_healthy", "health": health}
        created = self.mark_known_good("initial-known-good")
        return {"created": True, "snapshot_id": created["snapshot_id"]}

    def verify_integrity(self) -> dict:
        known = self.known_good()
        if known is None:
            return {"known_good": False, "changed": [], "missing": [], "added": []}
        expected = known["manifest"].get("files", {})
        current_files = {path.relative_to(self.root).as_posix(): path for path in self._source_files()}
        missing = sorted(path for path in expected if path not in current_files)
        changed = []
        for relative, expected_hash in expected.items():
            path = current_files.get(relative)
            if path is not None:
                try:
                    if _hash(path) != expected_hash:
                        changed.append(relative)
                except OSError:
                    changed.append(relative)
        added = sorted(path for path in current_files if path not in expected)
        return {
            "known_good": True,
            "snapshot_id": known["snapshot_id"],
            "changed": sorted(changed),
            "missing": missing,
            "added": added,
            "clean": not changed and not missing and not added,
        }

    def _authorize_restore(self, paths: list[str]) -> bool:
        if self.guardian is None:
            return True
        try:
            decision = self.guardian.authorize(
                "cure.restore", origin="cure-local", remote=False, confirmed=True,
                subject=f"{len(paths)} arquivo(s)", metadata={"paths": paths[:50]},
            )
            return bool(decision.allowed)
        except Exception:
            return False

    def restore_from_snapshot(self, snapshot_id: str, paths: list[str]) -> dict:
        meta = self._snapshot_meta(snapshot_id)
        allowed = set(meta.get("files", {}))
        requested = sorted({str(Path(item).as_posix()).lstrip("/") for item in paths if str(item).strip()})
        invalid = [item for item in requested if item not in allowed or ".." in Path(item).parts]
        if invalid:
            raise ValueError(f"Caminhos fora do snapshot/allowlist: {invalid}")
        if not self._authorize_restore(requested):
            raise PermissionError("Guardian bloqueou a restauração da Cura.")
        restored = []
        files_root = self.snapshots_dir / snapshot_id / "files"
        for relative in requested:
            source = files_root / relative
            target = self.root / relative
            if not source.is_file():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            restored.append(relative)
        self._event("restore", {"snapshot_id": snapshot_id, "paths": restored})
        return {"snapshot_id": snapshot_id, "restored": restored}

    def auto_repair(self) -> CureReport:
        known = self.known_good()
        if known is None:
            result = self.ensure_known_good()
            return CureReport(
                problem="known-good ausente",
                proposal="Criar baseline local após health check completo.",
                validated=bool(result.get("created")),
                applied=bool(result.get("created")),
                tests_passed=bool(result.get("created")),
                details=result,
            )

        integrity = self.verify_integrity()
        if integrity.get("clean"):
            return CureReport("nenhuma divergência", "Nenhuma correção necessária.", True, False, True, details=integrity)

        health = self.health_check(deep=True)
        # Mudança saudável não é apagada: pode ser atualização intencional.
        if health["healthy"]:
            report = CureReport(
                problem="arquivos diferem do snapshot, mas o sistema continua saudável",
                proposal="Não restaurar automaticamente; manter divergência registrada até a versão ser aceita como known-good.",
                validated=True,
                applied=False,
                tests_passed=True,
                details={"integrity": integrity, "health": health},
            )
            report.notes.append("A Cura nunca sobrescreve uma alteração saudável só por o hash ter mudado.")
            self._event("healthy_drift", integrity)
            return report

        failing_paths = {item.get("path") for item in health["failures"] if item.get("path")}
        candidates = sorted(set(integrity.get("changed", [])) | set(integrity.get("missing", [])))
        targeted = [path for path in candidates if path in failing_paths]
        if not targeted:
            targeted = candidates
        if not targeted:
            return CureReport(
                problem="falha detectada sem arquivo restaurável identificado",
                proposal="Manter diagnóstico; não aplicar correção especulativa.",
                validated=False,
                details={"integrity": integrity, "health": health},
            )

        pre = self.snapshot("pre-auto-repair", include_database=False)
        restored = self.restore_from_snapshot(known["snapshot_id"], targeted)
        after = self.health_check(deep=True)
        if after["healthy"]:
            report = CureReport(
                problem="corrupção local detectada",
                proposal="Restaurar arquivos falhos do snapshot conhecido como bom.",
                validated=True,
                applied=True,
                tests_passed=True,
                notes=[f"Snapshot de segurança pré-reparo: {pre['snapshot_id']}"],
                details={"before": health, "integrity": integrity, "restored": restored, "after": after},
            )
            self._event("auto_repair_success", {"restored": restored["restored"]})
            return report

        # Se a restauração piorar/não resolver, desfaz exatamente os arquivos tocados.
        self.restore_from_snapshot(pre["snapshot_id"], restored["restored"])
        rollback_health = self.health_check(deep=True)
        report = CureReport(
            problem="reparo local não validado",
            proposal="Rollback automático do reparo; manter diagnóstico para intervenção segura.",
            validated=False,
            applied=False,
            tests_passed=False,
            notes=["A tentativa de reparo foi revertida."],
            details={"before": health, "attempt_after": after, "rollback_health": rollback_health},
        )
        self._event("auto_repair_rollback", report.details)
        return report

    def watch_once(self, *, auto_repair: bool = True) -> dict:
        integrity = self.verify_integrity()
        if not integrity.get("known_good"):
            return self.ensure_known_good()
        if integrity.get("clean"):
            return {"healthy": True, "clean": True, "snapshot_id": integrity.get("snapshot_id")}
        if auto_repair:
            return asdict(self.auto_repair())
        return {"healthy": self.health_check(deep=True)["healthy"], "integrity": integrity}

    def start(self, *, interval_seconds: float = 60.0, auto_repair: bool = True) -> bool:
        if self._thread is not None and self._thread.is_alive():
            return False
        interval = max(15.0, float(interval_seconds))
        self._stop_event.clear()

        def loop():
            while not self._stop_event.wait(interval):
                try:
                    self.watch_once(auto_repair=auto_repair)
                except Exception as exc:
                    self._event("watch_error", {"error": f"{type(exc).__name__}: {exc}"})

        self._thread = threading.Thread(target=loop, daemon=True, name="STAR-Cura-Watchdog")
        self._thread.start()
        return True

    def stop(self):
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        self._thread = None

    def validate(self, report, tests_passed=False):
        report.validated = bool(tests_passed)
        report.tests_passed = bool(tests_passed)
        return report

    def apply(self, report):
        """Compatibilidade: correções arbitrárias continuam proibidas.

        Auto-reparo real acontece somente por ``auto_repair()``, que restaura arquivos
        exatos de snapshot conhecido como bom e valida o resultado.
        """
        if not report.validated:
            raise RuntimeError("Correção não validada; nenhuma alteração foi aplicada.")
        report.applied = False
        report.notes.append("Use auto_repair() para restauração controlada de snapshot; aplicação arbitrária continua bloqueada.")
        return report

    def stats(self) -> dict:
        known = self.known_good()
        return {
            "status": "active-local-guarded",
            "known_good": bool(known),
            "snapshot_id": known.get("snapshot_id") if known else None,
            "watchdog_running": bool(self._thread and self._thread.is_alive()),
            "offline": True,
            "github_required": False,
            "generative_code_repair": False,
            "safe_snapshot_restore": True,
            "database_quick_check": True,
        }
