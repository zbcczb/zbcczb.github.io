from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    machine_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    factory = relationship("Factory", back_populates="machines")
    statuses = relationship("MachineStatus", back_populates="machine", cascade="all, delete-orphan")
    alarms = relationship("AlarmRecord", back_populates="machine", cascade="all, delete-orphan")
    production_records = relationship("ProductionRecord", back_populates="machine", cascade="all, delete-orphan")
