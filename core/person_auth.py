"""Autenticação local de pessoas, separada do B26 recognition.

O provider persiste apenas derivação scrypt + salt em runtime local. Ele não é um
Permission Manager e nunca concede autorização operacional: apenas responde se um
challenge explícito corresponde à credencial cadastrada para um person_id.
"""
from __future__ import annotations

from hashlib import scrypt
import json
from pathlib import Path
import secrets
import threading
from typing import Any


class LocalPersonAuthenticator:
    MIN_SECRET_LENGTH = 6

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path or Path.cwd() / "runtime" / "security" / "person_credentials.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._records: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(payload, dict):
            self._records = {
                str(key): value
                for key, value in payload.items()
                if isinstance(value, dict) and value.get("salt") and value.get("digest")
            }

    def _save(self) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self._records, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    @staticmethod
    def _derive(secret: str, salt: bytes) -> str:
        return scrypt(
            str(secret).encode("utf-8"),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            dklen=32,
        ).hex()

    def enroll(self, person_id: str, secret: str, *, consent: bool = False) -> dict:
        person_id = str(person_id or "").strip()
        secret = str(secret or "")
        if not person_id:
            raise ValueError("person_id obrigatório")
        if not consent:
            raise PermissionError("cadastro de credencial exige consentimento explícito")
        if len(secret) < self.MIN_SECRET_LENGTH:
            raise ValueError(f"credencial deve possuir ao menos {self.MIN_SECRET_LENGTH} caracteres")
        salt = secrets.token_bytes(16)
        record = {
            "algorithm": "scrypt-n16384-r8-p1",
            "salt": salt.hex(),
            "digest": self._derive(secret, salt),
        }
        with self._lock:
            self._records[person_id] = record
            self._save()
        return {
            "person_id": person_id,
            "enrolled": True,
            "method": "local_scrypt_challenge",
            "secret_persisted": False,
            "operational_permission": False,
        }

    def revoke(self, person_id: str) -> bool:
        person_id = str(person_id or "").strip()
        with self._lock:
            existed = self._records.pop(person_id, None) is not None
            if existed:
                self._save()
        return existed

    def has_credential(self, person_id: str) -> bool:
        return str(person_id or "").strip() in self._records

    def verify(self, person_id: str, challenge: Any = None) -> dict:
        person_id = str(person_id or "").strip()
        if isinstance(challenge, dict):
            secret = str(challenge.get("secret") or challenge.get("pin") or challenge.get("passphrase") or "")
        else:
            secret = str(challenge or "")
        with self._lock:
            record = dict(self._records.get(person_id) or {})
        if not record:
            return {
                "person_id": person_id,
                "authenticated": False,
                "reason": "credential_not_enrolled",
                "method": "local_scrypt_challenge",
                "operational_permission": False,
            }
        try:
            salt = bytes.fromhex(str(record["salt"]))
            candidate = self._derive(secret, salt)
        except (KeyError, ValueError):
            return {
                "person_id": person_id,
                "authenticated": False,
                "reason": "credential_record_invalid",
                "method": "local_scrypt_challenge",
                "operational_permission": False,
            }
        authenticated = secrets.compare_digest(candidate, str(record.get("digest") or ""))
        return {
            "person_id": person_id,
            "authenticated": authenticated,
            "reason": "challenge_verified" if authenticated else "challenge_rejected",
            "method": "local_scrypt_challenge",
            "recognition_used_as_authentication": False,
            "operational_permission": False,
        }

    def stats(self) -> dict:
        return {
            "provider": "LocalPersonAuthenticator",
            "credential_records": len(self._records),
            "persistent_local_hashes": True,
            "raw_secrets_persisted": False,
            "recognition_is_authentication": False,
            "authentication_grants_permission": False,
        }
