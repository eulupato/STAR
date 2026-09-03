"""Configuração central de logs da STAR."""
from __future__ import annotations

import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger("star")
    if root.handlers:
        return root

    root.setLevel(level)
    formatter = logging.Formatter("[%(name)s] %(levelname)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    try:
        file_handler = logging.FileHandler(LOG_DIR / "star.log", encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
            )
        )
        root.addHandler(file_handler)
    except OSError:
        root.warning("Log em arquivo indisponível; mantendo somente console.")

    return root


def get_logger(component: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(f"star.{str(component).upper()}")
