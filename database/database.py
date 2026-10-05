from pathlib import Path
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Runtime normal continua usando o banco canônico da STAR. Testes e ferramentas
# isoladas podem apontar explicitamente para outro SQLite sem tocar em star.db.
_configured_path = str(os.getenv("STAR_DATABASE_PATH") or "").strip()
DATABASE_PATH = (
    Path(_configured_path).expanduser().resolve()
    if _configured_path
    else PROJECT_ROOT / "star.db"
)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()
