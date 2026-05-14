#!/usr/bin/env python3
"""Simulate an embroidery machine that uploads status every 5 seconds."""

from __future__ import annotations

import argparse
import random
import time
from datetime import datetime, timezone

import requests

STATUSES = ["running", "idle", "stopped", "alarm", "maintenance"]
PATTERNS = ["P001", "P002", "P003", "P004"]
ALARMS = ["THREAD_BREAK", "NEEDLE_BREAK", "MOTOR_OVERLOAD"]


def build_payload(machine_id: str, state: dict[str, float | int | str]) -> dict:
    status = random.choices(STATUSES, weights=[70, 12, 6, 8, 4], k=1)[0]
    rpm = random.randint(900, 1500) if status == "running" else random.randint(0, 250)

    if status == "running":
        state["current_stitches"] = int(state["current_stitches"]) + random.randint(350, 900)
        if random.random() < 0.25:
            state["finished_pieces"] = int(state["finished_pieces"]) + 1
        state["work_hours"] = round(float(state["work_hours"]) + (5 / 3600), 3)

    alarm_code = random.choice(ALARMS) if status == "alarm" else None

    return {
        "machine_id": machine_id,
        "status": status,
        "rpm": rpm,
        "current_stitches": state["current_stitches"],
        "finished_pieces": state["finished_pieces"],
        "work_hours": state["work_hours"],
        "alarm_code": alarm_code,
        "pattern_id": state["pattern_id"],
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload random machine status data to the FastAPI backend.")
    parser.add_argument("--url", default="http://localhost:8000/api/machine/status", help="Status upload endpoint")
    parser.add_argument("--machine-id", default="CBL001", help="External machine ID")
    parser.add_argument("--interval", type=float, default=5.0, help="Upload interval in seconds")
    args = parser.parse_args()

    state: dict[str, float | int | str] = {
        "current_stitches": random.randint(10_000, 50_000),
        "finished_pieces": random.randint(1, 30),
        "work_hours": round(random.uniform(0.5, 6.0), 2),
        "pattern_id": random.choice(PATTERNS),
    }

    print(f"Simulating machine {args.machine_id}; posting to {args.url} every {args.interval} seconds.")
    while True:
        payload = build_payload(args.machine_id, state)
        try:
            response = requests.post(args.url, json=payload, timeout=10)
            response.raise_for_status()
            print(f"[{datetime.now(timezone.utc).isoformat()}] uploaded: {payload} -> {response.status_code}")
        except requests.RequestException as exc:
            print(f"Upload failed: {exc}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
