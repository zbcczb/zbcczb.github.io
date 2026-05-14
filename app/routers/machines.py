from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Factory, Machine
from app.schemas import MachineCreate, MachineRead, MachineStatusRead, MachineStatusUpload, MachineStatsRead
from app.services.machine_service import (
    ensure_default_factory,
    get_machine_stats,
    get_status_response,
    list_factory_machines,
    list_machines,
    record_status,
)

router = APIRouter(tags=["machines"])


@router.post("/machine/status", response_model=MachineStatusRead, status_code=status.HTTP_201_CREATED)
def upload_machine_status(payload: MachineStatusUpload, db: Session = Depends(get_db)) -> dict:
    record_status(db, payload)
    status_response = get_status_response(db, payload.machine_id)
    if status_response is None:
        raise HTTPException(status_code=500, detail="Failed to read saved machine status")
    return status_response


@router.get("/machines", response_model=list[MachineRead])
def get_machines(db: Session = Depends(get_db)) -> list[dict]:
    return list_machines(db)


@router.post("/machines", response_model=MachineRead, status_code=status.HTTP_201_CREATED)
def create_machine(payload: MachineCreate, db: Session = Depends(get_db)) -> dict:
    existing = db.scalar(select(Machine).where(Machine.machine_id == payload.machine_id))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Machine already exists")

    if payload.factory_id is None:
        factory = ensure_default_factory(db)
    else:
        factory = db.get(Factory, payload.factory_id)
        if factory is None:
            raise HTTPException(status_code=404, detail="Factory not found")

    machine = Machine(
        machine_id=payload.machine_id,
        name=payload.name or payload.machine_id,
        model=payload.model,
        factory_id=factory.id,
    )
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return {
        "id": machine.id,
        "machine_id": machine.machine_id,
        "name": machine.name,
        "model": machine.model,
        "factory_id": machine.factory_id,
        "last_seen_at": machine.last_seen_at,
        "connectivity": "offline",
        "latest_status": None,
    }


@router.get("/machines/{machine_id}/status", response_model=MachineStatusRead)
def get_machine_status(machine_id: str, db: Session = Depends(get_db)) -> dict:
    status_response = get_status_response(db, machine_id)
    if status_response is None:
        raise HTTPException(status_code=404, detail="Machine status not found")
    return status_response


@router.get("/machines/{machine_id}/stats", response_model=MachineStatsRead)
def get_stats(
    machine_id: str,
    target_date: date = Query(..., alias="date", description="Production date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
) -> dict:
    stats = get_machine_stats(db, machine_id, target_date)
    if stats is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return stats


@router.get("/factories/{factory_id}/machines", response_model=list[MachineRead])
def get_factory_machines(factory_id: int, db: Session = Depends(get_db)) -> list[dict]:
    factory = db.get(Factory, factory_id)
    if factory is None:
        raise HTTPException(status_code=404, detail="Factory not found")
    return list_factory_machines(db, factory_id)
