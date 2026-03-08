"""CLI entry point for the podcast generation pipeline."""

import logging
import sys

from src.application.podcast_service import generate_podcast
from src.config import Settings
from src.domain.models import PipelineConfig
from src.exceptions import AudioWriteError, ConfigurationError, InputError, PodcastError, TTSError
from src.infrastructure.database import create_db_engine, get_session_factory
from src.infrastructure.database.models import Base
from src.infrastructure.database.repositories import HostRepository, StyleRepository, seed_defaults

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Parse CLI args, load config from DB, and run the pipeline."""
    source_files = sys.argv[1:]
    if not source_files:
        print("Usage: python main.py file1.md [file2.md ...]")
        sys.exit(1)

    try:
        settings = Settings()

        # Database setup
        engine = create_db_engine(settings.database_url)
        Base.metadata.create_all(engine)
        session_factory = get_session_factory(engine)

        with session_factory() as session:
            seed_defaults(session, settings)
            session.commit()

            # Load default hosts and style
            host_repo = HostRepository(session)
            style_repo = StyleRepository(session)

            hosts = host_repo.get_defaults()
            if len(hosts) != 2:
                print(f"Expected 2 default hosts, found {len(hosts)}.")
                sys.exit(1)

            styles = style_repo.get_defaults()
            if not styles:
                print("No default style found.")
                sys.exit(1)
            style = styles[0]

        # Build pipeline config (one source file at a time for now)
        config = PipelineConfig(
            hosts=hosts,
            style=style,
            source_file=source_files[0],
        )

        generate_podcast(config, settings, output_file="out.wav")

    except ConfigurationError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)
    except InputError as e:
        logger.error("Input error: %s", e)
        sys.exit(1)
    except TTSError as e:
        logger.error("TTS error: %s", e)
        sys.exit(1)
    except AudioWriteError as e:
        logger.error("Audio write error: %s", e)
        sys.exit(1)
    except PodcastError as e:
        logger.error("Error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
