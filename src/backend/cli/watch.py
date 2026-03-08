"""Standalone watcher CLI -- runs folder watcher without the web server."""

from __future__ import annotations

import logging
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.watcher.service import WatcherService
from src.config import Settings
from src.infrastructure.database.repositories import seed_defaults

logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point for ``python -m src watch``."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = Settings()  # type: ignore[call-arg]

    connect_args: dict[str, object] = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(settings.database_url, connect_args=connect_args)

    # Run Alembic migrations programmatically
    from alembic.config import Config as AlembicConfig
    from alembic import command as alembic_command

    alembic_cfg = AlembicConfig("alembic.ini")
    alembic_command.upgrade(alembic_cfg, "head")

    session_factory = sessionmaker(bind=engine)

    # Seed defaults
    session = session_factory()
    try:
        seed_defaults(session, settings)
        session.commit()
    finally:
        session.close()

    watcher = WatcherService(settings, session_factory)
    watcher.start()
    logger.info("Watcher running. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()


if __name__ == "__main__":
    main()
