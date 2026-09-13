"""STAR People — perfis pessoais locais, explícitos e auditáveis.

O sistema guarda informações fornecidas pelo usuário/perfil e metadados técnicos de
imagens no mesmo SQLite oficial da STAR. Não faz inferência de raça, religião,
saúde, orientação sexual, personalidade ou identidade biométrica a partir de foto.
Imagens são copiadas para runtime/people e nunca precisam sair do dispositivo.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

from sqlalchemy import text

from database.database import engine

ROOT = Path(__file__).resolve().parents[1]
PEOPLE_ROOT = ROOT / "runtime" / "people"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dump(value) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def _load(value):
    try:
        return json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}


def _slug(value: str) -> str:
    compact = re.sub(r"[^\wÀ-ÿ-]+", "-", str(value).strip().casefold(), flags=re.UNICODE).strip("-")
    return compact[:80] or "person"


def _dhash(path: Path) -> str | None:
    try:
        from PIL import Image
        with Image.open(path) as image:
            image = image.convert("L").resize((9, 8))
            pixels = list(image.getdata())
        bits = []
        for y in range(8):
            row = pixels[y * 9:(y + 1) * 9]
            bits.extend(row[x] > row[x + 1] for x in range(8))
        value = 0
        for bit in bits:
            value = (value << 1) | int(bit)
        return f"{value:016x}"
    except Exception:
        return None


class PeopleStore:
    def __init__(self, root: Path | str = PEOPLE_ROOT):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _ensure_schema(self):
        with engine.begin() as conn:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS star_people (
                person_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                aliases_json TEXT NOT NULL DEFAULT '[]',
                fields_json TEXT NOT NULL DEFAULT '{}',
                notes TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_star_people_name ON star_people(name)"))
            conn.execute(text("""CREATE TABLE IF NOT EXISTS star_people_assets (
                asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                local_path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                perceptual_hash TEXT,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                UNIQUE(person_id, sha256)
            )"""))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_people_assets_person ON star_people_assets(person_id)"))

    @staticmethod
    def parse_profile_text(text_value: str) -> dict:
        """Extrai apenas campos explicitamente rotulados; não infere traços ocultos."""
        text_value = str(text_value or "").strip()
        fields = {}
        free = []
        for line in text_value.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match(r"^([\wÀ-ÿ /_-]{2,40})\s*[:=-]\s*(.+)$", line, flags=re.UNICODE)
            if match:
                key = re.sub(r"\s+", "_", match.group(1).strip().casefold())[:48]
                fields[key] = match.group(2).strip()[:1000]
            else:
                free.append(line)
        if free:
            fields["profile_text"] = "\n".join(free)[:8000]
        return fields

    def add(self, name: str, *, aliases=None, fields=None, notes: str = "", source: str = "user") -> dict:
        name = str(name or "").strip()
        if not name:
            raise ValueError("Nome é obrigatório.")
        aliases = sorted({str(x).strip() for x in (aliases or []) if str(x).strip() and str(x).strip().casefold() != name.casefold()})
        now = _now()
        with engine.begin() as conn:
            result = conn.execute(text("""INSERT INTO star_people(name,aliases_json,fields_json,notes,source,created_at,updated_at)
                VALUES(:name,:aliases,:fields,:notes,:source,:now,:now)"""), {
                "name": name, "aliases": _dump(aliases), "fields": _dump(fields or {}),
                "notes": str(notes or "").strip(), "source": str(source or "user"), "now": now,
            })
            person_id = int(result.lastrowid)
        return self.get(person_id)

    def upsert(self, name: str, *, aliases=None, fields=None, notes: str = "", source: str = "user") -> dict:
        existing = self.find(name)
        if existing is None:
            return self.add(name, aliases=aliases, fields=fields, notes=notes, source=source)
        merged_aliases = sorted(set(existing["aliases"]) | {str(x).strip() for x in (aliases or []) if str(x).strip()})
        merged_fields = {**existing["fields"], **dict(fields or {})}
        merged_notes = str(notes or "").strip() or existing["notes"]
        with engine.begin() as conn:
            conn.execute(text("""UPDATE star_people SET aliases_json=:a,fields_json=:f,notes=:n,source=:s,updated_at=:u WHERE person_id=:id"""), {
                "a": _dump(merged_aliases), "f": _dump(merged_fields), "n": merged_notes,
                "s": str(source or existing["source"]), "u": _now(), "id": existing["person_id"],
            })
        return self.get(existing["person_id"])

    def ingest_profile(self, name: str, profile_text: str, *, aliases=None, notes: str = "", source: str = "profile") -> dict:
        fields = self.parse_profile_text(profile_text)
        return self.upsert(name, aliases=aliases, fields=fields, notes=notes, source=source)

    def _row(self, row) -> dict:
        item = dict(row)
        item["aliases"] = list(_load(item.pop("aliases_json", "[]")) or [])
        item["fields"] = dict(_load(item.pop("fields_json", "{}")) or {})
        return item

    def get(self, person_id: int) -> dict | None:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM star_people WHERE person_id=:id"), {"id": int(person_id)}).mappings().first()
            if row is None:
                return None
            assets = conn.execute(text("SELECT * FROM star_people_assets WHERE person_id=:id ORDER BY asset_id"), {"id": int(person_id)}).mappings().all()
        item = self._row(row)
        item["assets"] = [{**dict(a), "metadata": _load(a["metadata_json"])} for a in assets]
        return item

    def find(self, query: str) -> dict | None:
        needle = str(query or "").strip().casefold()
        if not needle:
            return None
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM star_people ORDER BY updated_at DESC")).mappings().all()
        for row in rows:
            item = self._row(row)
            names = {item["name"].casefold(), *(x.casefold() for x in item["aliases"])}
            if needle in names:
                return self.get(item["person_id"])
        for row in rows:
            item = self._row(row)
            if needle in item["name"].casefold() or any(needle in x.casefold() for x in item["aliases"]):
                return self.get(item["person_id"])
        return None

    def list(self, limit: int = 200) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM star_people ORDER BY name COLLATE NOCASE LIMIT :n"), {"n": max(1, min(int(limit), 1000))}).mappings().all()
        return [self._row(row) for row in rows]

    @staticmethod
    def _image_metadata(path: Path) -> dict:
        from PIL import Image, ExifTags
        with Image.open(path) as image:
            metadata = {
                "format": image.format,
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
            }
            try:
                exif = image.getexif()
                allowed = {"DateTime", "DateTimeOriginal", "Make", "Model", "Software", "Orientation"}
                readable = {}
                for key, value in exif.items():
                    name = ExifTags.TAGS.get(key, str(key))
                    if name in allowed:
                        readable[name] = str(value)[:500]
                if readable:
                    metadata["exif_public"] = readable
            except Exception:
                pass
        return metadata

    def add_image(self, person_id: int, image_path: str | Path, *, kind: str = "photo") -> dict:
        person = self.get(person_id)
        if person is None:
            raise KeyError(person_id)
        source = Path(image_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        metadata = self._image_metadata(source)
        raw = source.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        suffix = source.suffix.lower() if source.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"} else ".img"
        target_dir = self.root / f"{int(person_id):06d}-{_slug(person['name'])}"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{digest[:20]}{suffix}"
        if not target.exists():
            shutil.copy2(source, target)
        phash = _dhash(target)
        with engine.begin() as conn:
            conn.execute(text("""INSERT OR IGNORE INTO star_people_assets(person_id,kind,local_path,sha256,perceptual_hash,metadata_json,created_at)
                VALUES(:p,:k,:path,:sha,:ph,:meta,:now)"""), {
                "p": int(person_id), "k": str(kind), "path": str(target), "sha": digest,
                "ph": phash, "meta": _dump(metadata), "now": _now(),
            })
        return {"person_id": int(person_id), "local_path": str(target), "sha256": digest, "perceptual_hash": phash, "metadata": metadata}

    def enroll(self, name: str, *, image_path: str | Path | None = None, profile_text: str = "", aliases=None, notes: str = "") -> dict:
        person = self.ingest_profile(name, profile_text, aliases=aliases, notes=notes) if profile_text else self.upsert(name, aliases=aliases, notes=notes)
        if image_path:
            self.add_image(person["person_id"], image_path)
        return self.get(person["person_id"])

    def stats(self) -> dict:
        with engine.connect() as conn:
            people = int(conn.execute(text("SELECT COUNT(*) FROM star_people")).scalar_one())
            assets = int(conn.execute(text("SELECT COUNT(*) FROM star_people_assets")).scalar_one())
        return {
            "status": "active-local",
            "people": people,
            "assets": assets,
            "storage": "star.db + runtime/people",
            "network_required": False,
            "face_recognition": False,
            "image_fingerprint": "non-biometric dHash + SHA-256",
            "sensitive_trait_inference": False,
            "gps_exif_ingested": False,
        }
