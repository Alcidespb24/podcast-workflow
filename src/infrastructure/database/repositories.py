"""Repository classes that map ORM records to domain models."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import Settings
from src.domain.models import Host, Style
from src.infrastructure.database.models import HostRecord, StyleRecord


class HostRepository:
    """CRUD operations for hosts, returning domain models."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(record: HostRecord) -> Host:
        return Host(
            id=record.id,
            name=record.name,
            voice=record.voice,
            role=record.role,
        )

    def create(self, host: Host) -> Host:
        record = HostRecord(
            name=host.name,
            voice=host.voice,
            role=host.role,
        )
        self._session.add(record)
        self._session.flush()
        return self._to_domain(record)

    def get_by_id(self, host_id: int) -> Host | None:
        record = self._session.get(HostRecord, host_id)
        if record is None:
            return None
        return self._to_domain(record)

    def get_all(self) -> list[Host]:
        stmt = select(HostRecord).order_by(HostRecord.id)
        return [self._to_domain(r) for r in self._session.scalars(stmt)]

    def get_defaults(self) -> list[Host]:
        stmt = select(HostRecord).where(HostRecord.is_default.is_(True)).order_by(HostRecord.id)
        return [self._to_domain(r) for r in self._session.scalars(stmt)]

    def update(self, host_id: int, **fields: object) -> Host | None:
        record = self._session.get(HostRecord, host_id)
        if record is None:
            return None
        for key, value in fields.items():
            if hasattr(record, key):
                setattr(record, key, value)
        self._session.flush()
        return self._to_domain(record)

    def delete(self, host_id: int) -> bool:
        record = self._session.get(HostRecord, host_id)
        if record is None:
            return False
        self._session.delete(record)
        self._session.flush()
        return True


class StyleRepository:
    """CRUD operations for styles, returning domain models."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(record: StyleRecord) -> Style:
        return Style(
            id=record.id,
            name=record.name,
            tone=record.tone,
            personality_guidance=record.personality_guidance,
        )

    def create(self, style: Style) -> Style:
        record = StyleRecord(
            name=style.name,
            tone=style.tone,
            personality_guidance=style.personality_guidance,
        )
        self._session.add(record)
        self._session.flush()
        return self._to_domain(record)

    def get_by_id(self, style_id: int) -> Style | None:
        record = self._session.get(StyleRecord, style_id)
        if record is None:
            return None
        return self._to_domain(record)

    def get_all(self) -> list[Style]:
        stmt = select(StyleRecord).order_by(StyleRecord.id)
        return [self._to_domain(r) for r in self._session.scalars(stmt)]

    def get_defaults(self) -> list[Style]:
        stmt = select(StyleRecord).where(StyleRecord.is_default.is_(True)).order_by(StyleRecord.id)
        return [self._to_domain(r) for r in self._session.scalars(stmt)]

    def update(self, style_id: int, **fields: object) -> Style | None:
        record = self._session.get(StyleRecord, style_id)
        if record is None:
            return None
        for key, value in fields.items():
            if hasattr(record, key):
                setattr(record, key, value)
        self._session.flush()
        return self._to_domain(record)

    def delete(self, style_id: int) -> bool:
        record = self._session.get(StyleRecord, style_id)
        if record is None:
            return False
        self._session.delete(record)
        self._session.flush()
        return True


def seed_defaults(session: Session, settings: Settings) -> None:
    """Insert default hosts and style if the tables are empty. Idempotent."""
    host_count = session.scalar(select(HostRecord.id).limit(1))
    if host_count is None:
        session.add(
            HostRecord(
                name=settings.default_host_a_name,
                voice=settings.default_host_a_voice,
                role="host",
                is_default=True,
            )
        )
        session.add(
            HostRecord(
                name=settings.default_host_b_name,
                voice=settings.default_host_b_voice,
                role="co-host",
                is_default=True,
            )
        )

    style_count = session.scalar(select(StyleRecord.id).limit(1))
    if style_count is None:
        session.add(
            StyleRecord(
                name="Default",
                tone=settings.default_style_tone,
                is_default=True,
            )
        )

    session.flush()
