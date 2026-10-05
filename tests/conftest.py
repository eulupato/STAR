"""Isolamento global da suíte STAR.

A suíte nunca deve escrever no star.db real do usuário. O override é configurado
antes da coleta dos módulos de teste, então database.database cria o engine em um
SQLite temporário exclusivo desta execução.
"""
from __future__ import annotations

import atexit
import os
from pathlib import Path
import shutil
import tempfile


_TEST_DB_DIR = Path(tempfile.mkdtemp(prefix=f"star-pytest-{os.getpid()}-"))
os.environ.setdefault("STAR_DATABASE_PATH", str(_TEST_DB_DIR / "star-test.db"))


@atexit.register
def _cleanup_star_test_database() -> None:
    shutil.rmtree(_TEST_DB_DIR, ignore_errors=True)
