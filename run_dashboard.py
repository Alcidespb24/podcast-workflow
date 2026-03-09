"""Launch the dashboard with full DB wiring for manual testing."""

import os
import uvicorn
from pathlib import Path

# Provide defaults for fields not needed by the dashboard
os.environ.setdefault("BASE_URL", "https://localhost")
os.environ.setdefault("VAULT_OUTPUT_DIR", ".")

from src.config import load_settings
from src.infrastructure.database import create_db_engine, get_session_factory, run_migrations
from src.infrastructure.database.repositories import EpisodeRepository, seed_defaults
from src.backend.web.app import create_app
from src.backend.watcher.service import WatcherService

settings = load_settings()

Path("data").mkdir(exist_ok=True)
run_migrations(settings.database_url)
engine = create_db_engine(settings.database_url)
session_factory = get_session_factory(engine)

with session_factory() as session:
    seed_defaults(session, settings)
    session.commit()

def get_episodes():
    with session_factory() as s:
        return EpisodeRepository(s).get_all()

watcher_service = WatcherService(settings, session_factory)

app = create_app(settings, get_episodes=get_episodes, session_factory=session_factory, watcher_service=watcher_service)

if __name__ == "__main__":
    uvicorn.run(app, host=settings.dashboard_host, port=8000)
