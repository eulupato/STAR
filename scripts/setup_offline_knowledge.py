"""Configura a base de conhecimento offline real da STAR.

Não roda automaticamente no startup. Downloads grandes exigem comando explícito.

Exemplos:
  python scripts/setup_offline_knowledge.py status
  python scripts/setup_offline_knowledge.py catalog
  python scripts/setup_offline_knowledge.py download-wikipedia compact
  python scripts/setup_offline_knowledge.py download-wikipedia standard
  python scripts/setup_offline_knowledge.py import-facts arquivo.jsonl
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.knowledge_research_documents import RealKnowledgeMaterializer
from core.offline_knowledge import CATEGORY_SOURCES, OfflineKnowledgeService, SOURCE_DEFINITIONS
from database.cognitive_store import CognitiveStore


KIWIX_INDEX = "https://download.kiwix.org/zim/wikipedia/"
PROFILES = {
    "compact": re.compile(r"^wikipedia_pt_top_nopic_(\d{4}-\d{2})\.zim$"),
    "standard": re.compile(r"^wikipedia_pt_all_nopic_(\d{4}-\d{2})\.zim$"),
    "full": re.compile(r"^wikipedia_pt_all_maxi_(\d{4}-\d{2})\.zim$"),
}


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(str(href))


def resolve_latest(profile: str) -> tuple[str, str]:
    pattern = PROFILES[profile]
    response = requests.get(KIWIX_INDEX, timeout=30)
    response.raise_for_status()
    parser = LinkParser()
    parser.feed(response.text)
    matches = []
    for href in parser.links:
        filename = href.rsplit("/", 1)[-1]
        match = pattern.fullmatch(filename)
        if match:
            matches.append((match.group(1), filename))
    if not matches:
        raise RuntimeError(f"nenhum ZIM encontrado para perfil {profile}")
    _, filename = max(matches)
    return KIWIX_INDEX + filename, filename


def download(url: str, destination: Path) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    existing = partial.stat().st_size if partial.exists() else 0
    headers = {"Range": f"bytes={existing}-"} if existing else {}
    with requests.get(url, headers=headers, stream=True, timeout=(20, 120)) as response:
        if existing and response.status_code == 200:
            existing = 0
            partial.unlink(missing_ok=True)
        response.raise_for_status()
        mode = "ab" if existing and response.status_code == 206 else "wb"
        written = existing
        with partial.open(mode) as stream:
            for chunk in response.iter_content(chunk_size=8 * 1024 * 1024):
                if not chunk:
                    continue
                stream.write(chunk)
                written += len(chunk)
    partial.replace(destination)
    return {"path": str(destination), "bytes": written, "url": url}


def import_normalized_facts(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    store = CognitiveStore()
    grouped: dict[str, list[dict]] = {}
    read = rejected = 0
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if not line:
                continue
            read += 1
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                rejected += 1
                continue
            theme = str(item.pop("theme", "")).strip()
            if theme not in CATEGORY_SOURCES:
                rejected += 1
                continue
            grouped.setdefault(theme, []).append(item)
    result = {"read": read, "accepted": 0, "duplicates": 0, "rejected": rejected, "themes": {}}
    for theme, records in grouped.items():
        current = store.ingest_facts(theme, records, target_count=1_000_000_000)
        result["accepted"] += current["accepted"]
        result["duplicates"] += current["duplicates"]
        result["rejected"] += current["rejected"]
        result["themes"][theme] = current
    return result


def status() -> dict:
    store = CognitiveStore()
    materializer = RealKnowledgeMaterializer()
    materializer.ensure_namespaces(CATEGORY_SOURCES)
    service = OfflineKnowledgeService(store, real_materializer=materializer)
    return {
        "offline": service.stats(),
        "store": {
            "facts": store.stats()["facts"],
            "facts_fts_available": store.facts_fts_available,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="STAR offline knowledge setup")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("catalog")
    sub.add_parser("install-reader")
    download_parser = sub.add_parser("download-wikipedia")
    download_parser.add_argument("profile", choices=tuple(PROFILES))
    import_parser = sub.add_parser("import-facts")
    import_parser.add_argument("path")
    args = parser.parse_args()

    if args.command == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "catalog":
        print(json.dumps({
            "categories": CATEGORY_SOURCES,
            "sources": SOURCE_DEFINITIONS,
            "target_per_category": 1_000_000_000,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.command == "install-reader":
        command = [sys.executable, "-m", "pip", "install", "libzim>=3.13,<4"]
        print(json.dumps({
            "explicit_install": True,
            "package": "libzim>=3.13,<4",
            "purpose": "leitura/busca local de arquivos ZIM",
        }, ensure_ascii=False, indent=2))
        return subprocess.call(command)

    if args.command == "download-wikipedia":
        url, filename = resolve_latest(args.profile)
        destination = ROOT / "runtime" / "knowledge" / "zim" / filename
        print(json.dumps({
            "profile": args.profile,
            "resolved_url": url,
            "destination": str(destination),
            "automatic_startup_download": False,
        }, ensure_ascii=False, indent=2))
        result = download(url, destination)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    result = import_normalized_facts(Path(args.path).expanduser().resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
