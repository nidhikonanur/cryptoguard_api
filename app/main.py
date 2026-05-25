from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.db import init_db
from app.routes import audit, orders, transfers
from app.schemas import HealthResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CryptoGuard API",
    description="Mock crypto transfer and trade order risk-check API for portfolio use.",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(transfers.router)
app.include_router(orders.router)
app.include_router(audit.router)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", database="sqlite")
