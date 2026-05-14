from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MachineStatus(Base):
    __tablename__ = "machine_statuses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    rpm: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_stitches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    finished_pieces: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    work_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    alarm_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pattern_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False
    )

    machine = relationship("Machine", back_populates="statuses")
