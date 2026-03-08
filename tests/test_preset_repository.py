"""Tests for PresetRepository."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.domain.models import Preset
from src.infrastructure.database.models import Base, HostRecord, StyleRecord
from src.infrastructure.database.repositories import PresetRepository


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as s:
        # prerequisite records
        s.add(HostRecord(name="Joe", voice="Kore", role="host"))
        s.add(HostRecord(name="Jane", voice="Puck", role="co-host"))
        s.add(StyleRecord(name="Default", tone="informative"))
        s.flush()
        yield s


class TestPresetRepository:
    def test_create_returns_preset_with_id(self, session: Session):
        repo = PresetRepository(session)
        p = repo.create(Preset(folder_path="/notes/tech", host_a_id=1, host_b_id=2, style_id=1))
        assert p.id is not None
        assert p.folder_path == "/notes/tech"

    def test_get_by_id(self, session: Session):
        repo = PresetRepository(session)
        created = repo.create(Preset(folder_path="/notes/tech", host_a_id=1, host_b_id=2, style_id=1))
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.folder_path == "/notes/tech"

    def test_get_by_id_missing(self, session: Session):
        repo = PresetRepository(session)
        assert repo.get_by_id(999) is None

    def test_get_by_folder_path(self, session: Session):
        repo = PresetRepository(session)
        repo.create(Preset(folder_path="/notes/tech", host_a_id=1, host_b_id=2, style_id=1))
        found = repo.get_by_folder_path("/notes/tech")
        assert found is not None
        assert found.host_a_id == 1

    def test_get_by_folder_path_missing(self, session: Session):
        repo = PresetRepository(session)
        assert repo.get_by_folder_path("/nope") is None

    def test_get_all(self, session: Session):
        repo = PresetRepository(session)
        repo.create(Preset(folder_path="/a", host_a_id=1, host_b_id=2, style_id=1))
        repo.create(Preset(folder_path="/b", host_a_id=1, host_b_id=2, style_id=1))
        assert len(repo.get_all()) == 2

    def test_delete(self, session: Session):
        repo = PresetRepository(session)
        created = repo.create(Preset(folder_path="/notes/tech", host_a_id=1, host_b_id=2, style_id=1))
        assert repo.delete(created.id) is True
        assert repo.get_by_id(created.id) is None

    def test_delete_missing(self, session: Session):
        repo = PresetRepository(session)
        assert repo.delete(999) is False
