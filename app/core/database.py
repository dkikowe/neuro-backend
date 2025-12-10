from typing import Generator
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session


# Load environment variables from .env
load_dotenv()

# Fetch DATABASE_URL directly from .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_simple_migrations() -> None:
    """
    Простейшие idempotent-миграции для существующей БД без Alembic.
    Добавляет колонку generation_count и таблицу uploads, если их нет.
    """
    ddl_statements = [
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS generation_count INTEGER NOT NULL DEFAULT 0
        """,
        """
        CREATE TABLE IF NOT EXISTS uploads (
            id SERIAL PRIMARY KEY,
            before_url VARCHAR(512) NOT NULL,
            after_url VARCHAR(512),
            style VARCHAR(64),
            created_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW())
        )
        """,
        # Индексы для выборок по пользователю и id
        "CREATE INDEX IF NOT EXISTS ix_uploads_created_by ON uploads (created_by)",
        "CREATE INDEX IF NOT EXISTS ix_uploads_id ON uploads (id)",
        """
        ALTER TABLE uploads
        ADD COLUMN IF NOT EXISTS style VARCHAR(64)
        """,
    ]

    with engine.begin() as conn:
        for ddl in ddl_statements:
            conn.execute(text(ddl))

