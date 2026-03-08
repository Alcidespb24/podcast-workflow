"""Tests for Alembic migration idempotency."""

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from sqlalchemy import create_engine, inspect

from src.infrastructure.database import run_migrations

PROJECT_ROOT = "D:/Podcast Workflow"


def _make_alembic_config(db_url: str) -> AlembicConfig:
    config = AlembicConfig(f"{PROJECT_ROOT}/alembic.ini")
    config.set_main_option("sqlalchemy.url", db_url)
    config.set_main_option("script_location", f"{PROJECT_ROOT}/alembic")
    return config


def test_run_migrations_creates_tables(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    run_migrations(db_url)
    engine = create_engine(db_url)
    tables = inspect(engine).get_table_names()
    assert "hosts" in tables
    assert "styles" in tables
    assert "alembic_version" in tables


def test_run_migrations_idempotent(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    run_migrations(db_url)
    run_migrations(db_url)  # Second call must not raise
    engine = create_engine(db_url)
    tables = inspect(engine).get_table_names()
    assert "hosts" in tables
    assert "styles" in tables


def test_alembic_upgrade_after_run_migrations(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    run_migrations(db_url)
    # Simulate user running `alembic upgrade head` after main.py
    config = _make_alembic_config(db_url)
    alembic_command.upgrade(config, "head")  # Must not raise
    engine = create_engine(db_url)
    tables = inspect(engine).get_table_names()
    assert "hosts" in tables
    assert "styles" in tables
