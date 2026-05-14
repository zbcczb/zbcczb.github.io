from datetime import date, datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AlarmRecord, Factory, Machine, MachineStatus, ProductionRecord
from app.schemas import MachineStatusUpload

settings = get_settings()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_default_factory(db: Session) -> Factory:
    factory = db.scalar(select(Factory).where(Factory.code == settings.default_factory_code))
    if factory is None:
        factory = Factory(code=settings.default_factory_code, name=settings.default_factory_name)
        db.add(factory)
        db.flush()
    return factory


def get_or_create_machine(db: Session, external_machine_id: str) -> Machine:
    machine = db.scalar(select(Machine).where(Machine.machine_id == external_machine_id))
    if machine is None:
        factory = ensure_default_factory(db)
        machine = Machine(machine_id=external_machine_id, name=external_machine_id, factory_id=factory.id)
        db.add(machine)
        db.flush()
    return machine


def latest_status_for_machine(db: Session, machine_pk: int) -> MachineStatus | None:
    return db.scalar(
        select(MachineStatus)
        .where(MachineStatus.machine_id == machine_pk)
        .order_by(MachineStatus.received_at.desc(), MachineStatus.id.desc())
        .limit(1)
    )


def connectivity_for(machine: Machine, now: datetime | None = None) -> str:
    if machine.last_seen_at is None:
        return "offline"
    now = now or utc_now()
    last_seen = machine.last_seen_at
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    elapsed = (now - last_seen).total_seconds()
    return "online" if elapsed <= settings.offline_threshold_seconds else "offline"


def record_status(db: Session, payload: MachineStatusUpload) -> tuple[Machine, MachineStatus]:
    machine = get_or_create_machine(db, payload.machine_id)
    now = utc_now()
    status = MachineStatus(
        machine_id=machine.id,
        status=payload.status,
        rpm=payload.rpm,
        current_stitches=payload.current_stitches,
        finished_pieces=payload.finished_pieces,
        work_hours=payload.work_hours,
        alarm_code=payload.alarm_code,
        pattern_id=payload.pattern_id,
        device_timestamp=payload.timestamp,
        received_at=now,
    )
    db.add(status)
    machine.last_seen_at = now

    db.add(
        ProductionRecord(
            machine_id=machine.id,
            pattern_id=payload.pattern_id,
            production_date=payload.timestamp.date(),
            stitches=payload.current_stitches,
            finished_pieces=payload.finished_pieces,
            work_hours=payload.work_hours,
            recorded_at=payload.timestamp,
        )
    )

    if payload.alarm_code:
        db.add(
            AlarmRecord(
                machine_id=machine.id,
                alarm_code=payload.alarm_code,
                message=f"Machine reported alarm {payload.alarm_code}",
                occurred_at=payload.timestamp,
            )
        )

    db.commit()
    db.refresh(machine)
    db.refresh(status)
    return machine, status


def list_machines(db: Session) -> list[dict]:
    machines = db.scalars(select(Machine).order_by(Machine.machine_id)).all()
    result = []
    for machine in machines:
        latest_status = latest_status_for_machine(db, machine.id)
        result.append(
            {
                "id": machine.id,
                "machine_id": machine.machine_id,
                "name": machine.name,
                "model": machine.model,
                "factory_id": machine.factory_id,
                "last_seen_at": machine.last_seen_at,
                "connectivity": connectivity_for(machine),
                "latest_status": latest_status.status if latest_status else None,
            }
        )
    return result


def list_factory_machines(db: Session, factory_id: int) -> list[dict]:
    machines = db.scalars(select(Machine).where(Machine.factory_id == factory_id).order_by(Machine.machine_id)).all()
    result = []
    for machine in machines:
        latest_status = latest_status_for_machine(db, machine.id)
        result.append(
            {
                "id": machine.id,
                "machine_id": machine.machine_id,
                "name": machine.name,
                "model": machine.model,
                "factory_id": machine.factory_id,
                "last_seen_at": machine.last_seen_at,
                "connectivity": connectivity_for(machine),
                "latest_status": latest_status.status if latest_status else None,
            }
        )
    return result


def get_status_response(db: Session, external_machine_id: str) -> dict | None:
    machine = db.scalar(select(Machine).where(Machine.machine_id == external_machine_id))
    if machine is None:
        return None
    status = latest_status_for_machine(db, machine.id)
    if status is None:
        return None
    effective_status = status.status if connectivity_for(machine) == "online" else "offline"
    return {
        "machine_id": machine.machine_id,
        "status": effective_status,
        "connectivity": connectivity_for(machine),
        "rpm": status.rpm,
        "current_stitches": status.current_stitches,
        "finished_pieces": status.finished_pieces,
        "work_hours": status.work_hours,
        "alarm_code": status.alarm_code,
        "pattern_id": status.pattern_id,
        "timestamp": status.device_timestamp,
        "received_at": status.received_at,
        "last_seen_at": machine.last_seen_at,
    }


def get_machine_stats(db: Session, external_machine_id: str, target_date: date) -> dict | None:
    machine = db.scalar(select(Machine).where(Machine.machine_id == external_machine_id))
    if machine is None:
        return None

    start_dt = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(target_date, time.max, tzinfo=timezone.utc)

    production = db.execute(
        select(
            func.max(ProductionRecord.stitches),
            func.max(ProductionRecord.finished_pieces),
            func.max(ProductionRecord.work_hours),
        ).where(ProductionRecord.machine_id == machine.id, ProductionRecord.production_date == target_date)
    ).one()
    avg_rpm = db.scalar(
        select(func.avg(MachineStatus.rpm)).where(
            MachineStatus.machine_id == machine.id,
            MachineStatus.device_timestamp >= start_dt,
            MachineStatus.device_timestamp <= end_dt,
        )
    )
    alarm_count = db.scalar(
        select(func.count(AlarmRecord.id)).where(
            AlarmRecord.machine_id == machine.id,
            AlarmRecord.occurred_at >= start_dt,
            AlarmRecord.occurred_at <= end_dt,
        )
    )
    latest_pattern_id = db.scalar(
        select(MachineStatus.pattern_id)
        .where(
            MachineStatus.machine_id == machine.id,
            MachineStatus.device_timestamp >= start_dt,
            MachineStatus.device_timestamp <= end_dt,
        )
        .order_by(MachineStatus.device_timestamp.desc(), MachineStatus.id.desc())
        .limit(1)
    )

    return {
        "machine_id": machine.machine_id,
        "date": target_date,
        "connectivity": connectivity_for(machine),
        "total_stitches": production[0] or 0,
        "finished_pieces": production[1] or 0,
        "work_hours": production[2] or 0.0,
        "average_rpm": round(float(avg_rpm or 0), 2),
        "alarm_count": int(alarm_count or 0),
        "latest_pattern_id": latest_pattern_id,
    }
