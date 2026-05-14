from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MachineRunStatus = Literal["running", "idle", "stopped", "alarm", "maintenance"]
ConnectivityStatus = Literal["online", "offline"]


class FactoryRead(BaseModel):
    id: int
    code: str
    name: str
    location: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MachineCreate(BaseModel):
    machine_id: str = Field(..., examples=["CBL001"])
    name: str | None = Field(default=None, examples=["Embroidery Machine 1"])
    model: str | None = Field(default=None, examples=["CBL-1206"])
    factory_id: int | None = Field(default=None, examples=[1])


class MachineRead(BaseModel):
    id: int
    machine_id: str
    name: str | None = None
    model: str | None = None
    factory_id: int
    last_seen_at: datetime | None = None
    connectivity: ConnectivityStatus
    latest_status: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MachineStatusUpload(BaseModel):
    machine_id: str = Field(..., examples=["CBL001"])
    status: MachineRunStatus = Field(..., examples=["running"])
    rpm: int = Field(..., ge=0, examples=[1500])
    current_stitches: int = Field(..., ge=0, examples=[58200])
    finished_pieces: int = Field(..., ge=0, examples=[36])
    work_hours: float = Field(..., ge=0, examples=[7.5])
    alarm_code: str | None = Field(default=None, examples=[None])
    pattern_id: str | None = Field(default=None, examples=["P001"])
    timestamp: datetime = Field(..., examples=["2026-05-14T10:30:00Z"])


class MachineStatusRead(BaseModel):
    machine_id: str
    status: str
    connectivity: ConnectivityStatus
    rpm: int
    current_stitches: int
    finished_pieces: int
    work_hours: float
    alarm_code: str | None = None
    pattern_id: str | None = None
    timestamp: datetime
    received_at: datetime
    last_seen_at: datetime | None = None


class MachineStatsRead(BaseModel):
    machine_id: str
    date: date
    connectivity: ConnectivityStatus
    total_stitches: int
    finished_pieces: int
    work_hours: float
    average_rpm: float
    alarm_count: int
    latest_pattern_id: str | None = None
