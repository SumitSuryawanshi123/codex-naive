from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from common.config import SERVICE_VERSION
from common.feature_flags import get_flags, maybe_random_api_failure, set_flags


def configure_app(app: FastAPI, service_name: str) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def random_failure_middleware(request: Request, call_next):
        await maybe_random_api_failure(request)
        return await call_next(request)

    @app.get("/health", tags=["System"])
    async def health():
        return {"service": service_name, "status": "ok", "version": SERVICE_VERSION}

    @app.get("/feature-flags", tags=["System"])
    async def read_feature_flags():
        return get_flags()

    @app.patch("/feature-flags", tags=["System"])
    async def update_feature_flags(updates: dict[str, bool]):
        return set_flags(updates)

