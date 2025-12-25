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
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS status VARCHAR(64) NOT NULL DEFAULT 'active'
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS email_verification_token_hash VARCHAR(128)
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS email_verification_expires_at TIMESTAMP WITHOUT TIME ZONE
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS last_verification_sent_at TIMESTAMP WITHOUT TIME ZONE
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS reset_token_hash VARCHAR(128)
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS reset_token_expires_at TIMESTAMP WITHOUT TIME ZONE
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
        """
        ALTER TABLE uploads
        ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITHOUT TIME ZONE
        """,
        """
        ALTER TABLE uploads
        ADD COLUMN IF NOT EXISTS days_left INTEGER
        """,
        """
        CREATE TABLE IF NOT EXISTS generations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            email VARCHAR(255) NOT NULL,
            remaining_std INTEGER NOT NULL DEFAULT 1,
            used_std INTEGER NOT NULL DEFAULT 0,
            remaining_hd INTEGER NOT NULL DEFAULT 0,
            used_hd INTEGER NOT NULL DEFAULT 0,
            current_plan VARCHAR(64) NOT NULL DEFAULT 'free',
            purchased_at TIMESTAMP WITHOUT TIME ZONE,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW()),
            CONSTRAINT uq_generations_user_id UNIQUE (user_id),
            CONSTRAINT uq_generations_email UNIQUE (email)
        )
        """,
        """
        ALTER TABLE generations
        ADD COLUMN IF NOT EXISTS remaining_std INTEGER NOT NULL DEFAULT 1
        """,
        """
        ALTER TABLE generations
        ADD COLUMN IF NOT EXISTS used_std INTEGER NOT NULL DEFAULT 0
        """,
        """
        ALTER TABLE generations
        ADD COLUMN IF NOT EXISTS remaining_hd INTEGER NOT NULL DEFAULT 0
        """,
        """
        ALTER TABLE generations
        ADD COLUMN IF NOT EXISTS used_hd INTEGER NOT NULL DEFAULT 0
        """,
        """
        ALTER TABLE generations
        ADD COLUMN IF NOT EXISTS plan_expires_at TIMESTAMP WITHOUT TIME ZONE
        """,
        """
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            inv_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            plan_id VARCHAR(64),
            amount NUMERIC(12, 2) NOT NULL,
            description VARCHAR(512),
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW()),
            paid_at TIMESTAMP WITHOUT TIME ZONE,
            CONSTRAINT uq_payments_inv_id UNIQUE (inv_id)
        )
        """,
    ]

    with engine.begin() as conn:
        for ddl in ddl_statements:
            conn.execute(text(ddl))

