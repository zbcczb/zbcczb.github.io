from fastapi import FastAPI

from app.config import get_settings
from app.routers import machines_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend MVP for an embroidery machine smart factory. "
        "Devices upload telemetry over HTTP now; MQTT can be added later as another ingestion adapter."
    ),
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(machines_router, prefix=settings.api_prefix)
