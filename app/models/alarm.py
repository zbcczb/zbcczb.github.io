from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AlarmRecord(Base):
    __tablename__ = "alarm_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), index=True, nullable=False)
    alarm_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    machine = relationship("Machine", back_populates="alarms")
