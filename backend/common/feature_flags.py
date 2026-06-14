from __future__ import annotations

import asyncio
import os
import random
from typing import Any

from fastapi import HTTPException, Request

from common.config import PAYMENT_TIMEOUT_SECONDS


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "enabled"}


DEFAULT_FLAGS: dict[str, bool] = {
    "slow_recommendation_service": _env_bool("SLOW_RECOMMENDATION_SERVICE"),
    "payment_timeout": _env_bool("PAYMENT_TIMEOUT"),
    "driver_allocation_failure": _env_bool("DRIVER_ALLOCATION_FAILURE"),
    "random_api_failures": _env_bool("RANDOM_API_FAILURES"),
    "database_query_delay": _env_bool("DATABASE_QUERY_DELAY"),
}

FLAGS = DEFAULT_FLAGS.copy()


def get_flags() -> dict[str, bool]:
    return FLAGS.copy()


def set_flags(updates: dict[str, Any]) -> dict[str, bool]:
    for key, value in updates.items():
        if key in FLAGS and value is not None:
            FLAGS[key] = bool(value)
    return get_flags()


async def maybe_database_delay() -> None:
    if FLAGS["database_query_delay"]:
        await asyncio.sleep(random.uniform(0.35, 1.6))


async def maybe_slow_recommendation() -> None:
    if FLAGS["slow_recommendation_service"]:
        await asyncio.sleep(random.uniform(2.5, 5.5))


async def maybe_payment_timeout() -> None:
    if FLAGS["payment_timeout"]:
        await asyncio.sleep(PAYMENT_TIMEOUT_SECONDS)
        raise HTTPException(status_code=504, detail="Payment processor timed out")


async def maybe_driver_allocation_failure() -> None:
    if FLAGS["driver_allocation_failure"]:
        await asyncio.sleep(random.uniform(0.4, 1.2))
        raise HTTPException(status_code=503, detail="No drivers available for this zone")


async def maybe_random_api_failure(request: Request) -> None:
    if not FLAGS["random_api_failures"]:
        return
    if request.url.path in {"/health", "/feature-flags"}:
        return
    if random.random() < 0.12:
        raise HTTPException(status_code=503, detail="Transient upstream failure")

