from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from common.api import configure_app
from common.data_store import (
    address_to_location,
    drivers,
    get_restaurant,
    haversine_km,
    route_between,
)
from common.feature_flags import (
    maybe_database_delay,
    maybe_driver_allocation_failure,
)


app = FastAPI(
    title="Food Delivery Service",
    description="Driver allocation, ETA calculation, route generation, and delivery tracking.",
    version="1.0.0",
)
configure_app(app, "delivery-service")

ALLOCATIONS: dict[str, dict[str, Any]] = {}


class AllocateDeliveryRequest(BaseModel):
    order_id: str
    restaurant_id: str
    customer_address: str = Field(min_length=8)
    customer_location: dict[str, float] | None = None


class StatusUpdateRequest(BaseModel):
    status: Literal["assigned", "arrived", "picked_up", "nearby", "delivered", "cancelled"]


def _available_drivers() -> list[dict[str, Any]]:
    return [driver for driver in drivers() if driver["status"] == "available"]


def _progress_for(allocation: dict[str, Any]) -> dict[str, Any]:
    created = datetime.fromisoformat(allocation["created_at"])
    eta_time = datetime.fromisoformat(allocation["eta_at"])
    total_seconds = max(1, (eta_time - created).total_seconds())
    elapsed = max(0, (datetime.now(timezone.utc) - created).total_seconds())
    progress = min(100, int(elapsed / total_seconds * 100))
    manual = allocation.get("manual_status")
    if manual:
        status = manual
        progress = max(progress, {"assigned": 10, "arrived": 32, "picked_up": 58, "nearby": 86, "delivered": 100, "cancelled": progress}.get(manual, progress))
    elif progress >= 100:
        status = "delivered"
    elif progress >= 78:
        status = "nearby"
    elif progress >= 48:
        status = "picked_up"
    elif progress >= 22:
        status = "arrived"
    else:
        status = "assigned"
    remaining = max(0, int((eta_time - datetime.now(timezone.utc)).total_seconds() // 60))
    return {"status": status, "progress": progress, "eta_minutes": remaining}


@app.get("/drivers", tags=["Drivers"])
async def list_drivers(status: str | None = None):
    await maybe_database_delay()
    result = drivers()
    if status:
        result = [driver for driver in result if driver["status"] == status]
    return {"items": result, "total": len(result)}


@app.post("/deliveries/allocate", tags=["Deliveries"])
async def allocate_delivery(payload: AllocateDeliveryRequest):
    await maybe_driver_allocation_failure()
    await maybe_database_delay()
    restaurant = get_restaurant(payload.restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    available = _available_drivers()
    if not available:
        raise HTTPException(status_code=503, detail="No drivers available")

    restaurant_location = restaurant["location"]
    customer_location = payload.customer_location or address_to_location(payload.customer_address)
    driver = min(
        available,
        key=lambda item: haversine_km(item["location"], restaurant_location),
    )
    distance_km = haversine_km(restaurant_location, customer_location)
    driver_distance_km = haversine_km(driver["location"], restaurant_location)
    eta_minutes = max(14, int((distance_km + driver_distance_km) * random.uniform(5.8, 8.6)) + 8)
    allocation = {
        "id": f"del_{uuid.uuid4().hex[:12]}",
        "order_id": payload.order_id,
        "restaurant_id": payload.restaurant_id,
        "driver": driver,
        "status": "assigned",
        "distance_km": distance_km,
        "pickup_distance_km": driver_distance_km,
        "eta_minutes": eta_minutes,
        "route": route_between(restaurant_location, customer_location),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "eta_at": (datetime.now(timezone.utc) + timedelta(minutes=eta_minutes)).isoformat(),
    }
    ALLOCATIONS[payload.order_id] = allocation
    return allocation


@app.get("/deliveries/{order_id}/tracking", tags=["Tracking"])
async def order_tracking(order_id: str):
    await maybe_database_delay()
    allocation = ALLOCATIONS.get(order_id)
    if not allocation:
        raise HTTPException(status_code=404, detail="Delivery not found")
    progress = _progress_for(allocation)
    return {
        **allocation,
        "status": progress["status"],
        "progress": progress["progress"],
        "eta_minutes": progress["eta_minutes"],
    }


@app.patch("/deliveries/{order_id}/status", tags=["Tracking"])
async def update_delivery_status(order_id: str, payload: StatusUpdateRequest):
    await maybe_database_delay()
    allocation = ALLOCATIONS.get(order_id)
    if not allocation:
        raise HTTPException(status_code=404, detail="Delivery not found")
    allocation["manual_status"] = payload.status
    allocation["status"] = payload.status
    allocation["updated_at"] = datetime.now(timezone.utc).isoformat()
    return await order_tracking(order_id)


@app.get("/deliveries/{order_id}/route", tags=["Tracking"])
async def delivery_route(order_id: str):
    await maybe_database_delay()
    allocation = ALLOCATIONS.get(order_id)
    if not allocation:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return {
        "order_id": order_id,
        "route": allocation["route"],
        "distance_km": allocation["distance_km"],
    }

@app.post("/eta", tags=["Tracking"])
async def calculate_eta(payload: AllocateDeliveryRequest):
    await maybe_database_delay()
    restaurant = get_restaurant(payload.restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    customer_location = payload.customer_location or address_to_location(payload.customer_address)
    distance_km = haversine_km(restaurant["location"], customer_location)
    eta_minutes = max(10, int(distance_km * random.uniform(6.0, 8.0)) + 6)
    return {"restaurant_id": payload.restaurant_id, "distance_km": distance_km, "eta_minutes": eta_minutes}

