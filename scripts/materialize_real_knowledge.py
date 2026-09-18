"""Materializa conhecimento real local na STAR sem contar variações lógicas.

Uso:
  python scripts/materialize_real_knowledge.py status
  python scripts/materialize_real_knowledge.py add <namespace> <formato> <source_type> <license> <arquivo>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.knowledge_research_documents import RealKnowledgeMaterializer


def main() -> int:
    parser = argparse.ArgumentParser(description="STAR real knowledge materializer")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status")

    add = sub.add_parser("add")
    add.add_argument("namespace")
    add.add_argument("source_format")
    add.add_argument("source_type")
    add.add_argument("license_name")
    add.add_argument("path")

    args = parser.parse_args()
    materializer = RealKnowledgeMaterializer()

    if args.command == "status":
        print(json.dumps(materializer.status(), ensure_ascii=False, indent=2))
        return 0

    result = materializer.register_source(
        args.namespace,
        args.path,
        source_format=args.source_format,
        source_type=args.source_type,
        license_name=args.license_name,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
