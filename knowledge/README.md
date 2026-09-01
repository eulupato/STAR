# STAR Knowledge

A V3 usa `knowledge/` como subsistema, não como pasta de textos soltos.

- `entities.py` — modelo genérico;
- `store.py` — SQLite local e índices;
- `graph.py` — relações;
- `engine.py` — busca e resposta;
- `importers/` — ingestão reutilizável;
- `packs/` — manifests e seeds portáteis;
- `local/` — banco, PDFs derivados e cache local (gitignored).

A GUI nunca deve consultar SQL diretamente.
