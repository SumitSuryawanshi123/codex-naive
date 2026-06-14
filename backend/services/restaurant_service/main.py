from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from common.api import configure_app
from common.config import DELIVERY_SERVICE_URL, HTTP_TIMEOUT_SECONDS, PAYMENT_SERVICE_URL
from common.data_store import (
    categories,
    cuisines,
    get_menu_item,
    get_restaurant,
    menu_for_restaurant,
    menu_items,
    orders,
    restaurants,
)
from common.feature_flags import maybe_database_delay, maybe_slow_recommendation
from common.pricing import money, price_order


app = FastAPI(
    title="Food Delivery Restaurant Service",
    description="Restaurant discovery, menus, recommendations, and checkout orchestration.",
    version="1.0.0",
)
configure_app(app, "restaurant-service")

LIVE_ORDERS: dict[str, dict[str, Any]] = {}


class CartLine(BaseModel):
    menu_item_id: str
    quantity: int = Field(ge=1, le=20)


class Customer(BaseModel):
    name: str = Field(min_length=2)
    phone: str = Field(min_length=7)
    address: str = Field(min_length=8)
    location: dict[str, float] | None = None


class CreateOrderRequest(BaseModel):
    restaurant_id: str
    customer: Customer
    items: list[CartLine] = Field(min_length=1)
    payment_method: Literal["card", "upi", "wallet", "cash"] = "card"
    coupon_code: str | None = None
    customer_id: str = "guest"


def _restaurant_matches_query(restaurant: dict[str, Any], query: str) -> bool:
    needle = query.strip().lower()
    if not needle:
        return True
    fields = [
        restaurant["name"],
        restaurant["neighborhood"],
        " ".join(restaurant["cuisines"]),
    ]
    return any(needle in field.lower() for field in fields)


def _serialize_restaurant(restaurant: dict[str, Any]) -> dict[str, Any]:
    menu = menu_for_restaurant(restaurant["id"])
    popular = sorted(menu, key=lambda item: item["popularity"], reverse=True)[:3]
    return {
        **restaurant,
        "popular_items": popular,
        "menu_count": len(menu),
    }


def _paginate(items: list[dict[str, Any]], page: int, limit: int) -> dict[str, Any]:
    start = (page - 1) * limit
    end = start + limit
    return {
        "items": items[start:end],
        "total": len(items),
        "page": page,
        "limit": limit,
        "has_more": end < len(items),
    }


@app.get("/restaurants", tags=["Restaurants"])
async def list_restaurants(
    q: str = "",
    cuisine: str | None = None,
    category: str | None = None,
    min_rating: float = Query(default=0, ge=0, le=5),
    max_delivery_fee: float | None = Query(default=None, ge=0),
    sort_by: Literal["recommended", "rating", "delivery_time", "delivery_fee"] = "recommended",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=12, ge=1, le=50),
):
    await maybe_database_delay()
    result = [_serialize_restaurant(item) for item in restaurants()]
    result = [item for item in result if _restaurant_matches_query(item, q)]
    if cuisine:
        result = [item for item in result if cuisine in item["cuisines"]]
    if category:
        restaurant_ids = {
            item["restaurant_id"] for item in menu_items() if item["category"].lower() == category.lower()
        }
        result = [item for item in result if item["id"] in restaurant_ids]
    result = [item for item in result if item["rating"] >= min_rating]
    if max_delivery_fee is not None:
        result = [item for item in result if item["delivery_fee"] <= max_delivery_fee]

    if sort_by == "rating":
        result.sort(key=lambda item: item["rating"], reverse=True)
    elif sort_by == "delivery_time":
        result.sort(key=lambda item: item["delivery_time_min"])
    elif sort_by == "delivery_fee":
        result.sort(key=lambda item: item["delivery_fee"])
    else:
        result.sort(key=lambda item: (not item["promoted"], -item["rating"], item["delivery_time_min"]))
    return _paginate(result, page, limit)


@app.get("/restaurants/{restaurant_id}", tags=["Restaurants"])
async def restaurant_details(restaurant_id: str):
    await maybe_database_delay()
    restaurant = get_restaurant(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return _serialize_restaurant(restaurant)


@app.get("/restaurants/{restaurant_id}/menu", tags=["Menus"])
async def restaurant_menu(
    restaurant_id: str,
    q: str = "",
    category: str | None = None,
    vegetarian: bool | None = None,
):
    await maybe_database_delay()
    if not get_restaurant(restaurant_id):
        raise HTTPException(status_code=404, detail="Restaurant not found")
    result = menu_for_restaurant(restaurant_id)
    needle = q.strip().lower()
    if needle:
        result = [
            item
            for item in result
            if needle in item["name"].lower() or needle in item["description"].lower()
        ]
    if category:
        result = [item for item in result if item["category"].lower() == category.lower()]
    if vegetarian is not None:
        result = [item for item in result if item["vegetarian"] is vegetarian]
    result.sort(key=lambda item: (item["category"], -item["popularity"]))
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in result:
        grouped.setdefault(item["category"], []).append(item)
    return {"items": result, "groups": grouped, "total": len(result)}


@app.get("/search/restaurants", tags=["Search"])
async def search_restaurants(q: str = Query(min_length=1), limit: int = Query(default=10, ge=1, le=25)):
    await maybe_database_delay()
    result = [_serialize_restaurant(item) for item in restaurants() if _restaurant_matches_query(item, q)]
    result.sort(key=lambda item: item["rating"], reverse=True)
    return {"items": result[:limit], "total": len(result)}


@app.get("/search/menu", tags=["Search"])
async def search_food_items(q: str = Query(min_length=1), limit: int = Query(default=20, ge=1, le=50)):
    await maybe_database_delay()
    needle = q.strip().lower()
    result = [
        {
            **item,
            "restaurant": get_restaurant(item["restaurant_id"]),
        }
        for item in menu_items()
        if needle in item["name"].lower()
        or needle in item["description"].lower()
        or needle in item["category"].lower()
    ]
    result.sort(key=lambda item: item["popularity"], reverse=True)
    return {"items": result[:limit], "total": len(result)}


@app.get("/categories", tags=["Discovery"])
async def list_categories():
    await maybe_database_delay()
    counts = {category: 0 for category in categories()}
    for item in menu_items():
        counts[item["category"]] += 1
    return {
        "items": [{"name": category, "count": counts[category]} for category in categories()],
        "cuisines": cuisines(),
    }


@app.get("/recommendations", tags=["Discovery"])
async def recommendations(user_id: str = "guest", limit: int = Query(default=8, ge=1, le=30)):
    await maybe_slow_recommendation()
    await maybe_database_delay()
    previous = [order for order in orders() if order["customer_id"] == user_id]
    preferred_cuisines: set[str] = set()
    for order in previous[-5:]:
        restaurant = get_restaurant(order["restaurant_id"])
        if restaurant:
            preferred_cuisines.update(restaurant["cuisines"])

    candidates = [_serialize_restaurant(item) for item in restaurants()]
    candidates.sort(
        key=lambda item: (
            not bool(preferred_cuisines.intersection(item["cuisines"])),
            not item["promoted"],
            -item["rating"],
            item["delivery_time_min"],
        )
    )
    return {
        "items": candidates[:limit],
        "strategy": "recent-cuisine-affinity" if preferred_cuisines else "popular-near-you",
    }


def _build_order_items(payload: CreateOrderRequest) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for line in payload.items:
        item = get_menu_item(line.menu_item_id)
        if not item or item["restaurant_id"] != payload.restaurant_id:
            raise HTTPException(status_code=400, detail=f"Invalid menu item: {line.menu_item_id}")
        selected.append(
            {
                "id": item["id"],
                "name": item["name"],
                "category": item["category"],
                "image_url": item["image_url"],
                "quantity": line.quantity,
                "price": item["price"],
                "line_total": money(item["price"] * line.quantity),
            }
        )
    return selected


async def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail=f"Timed out calling {url}") from exc
    except httpx.HTTPStatusError as exc:
        detail: Any
        try:
            detail = exc.response.json()
        except ValueError:
            detail = exc.response.text
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Unable to reach {url}") from exc


async def _get_json(url: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Unable to reach {url}") from exc


@app.post("/orders", tags=["Orders"])
async def create_order(payload: CreateOrderRequest):
    await maybe_database_delay()
    restaurant = get_restaurant(payload.restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    order_id = f"ord_{uuid.uuid4().hex[:12]}"
    selected_items = _build_order_items(payload)
    totals = price_order(restaurant, selected_items, payload.coupon_code)
    now = datetime.now(timezone.utc).isoformat()
    order = {
        "id": order_id,
        "status": "pricing_confirmed",
        "customer_id": payload.customer_id,
        "customer": payload.customer.model_dump(),
        "restaurant": restaurant,
        "items": selected_items,
        "totals": totals,
        "payment": None,
        "delivery": None,
        "created_at": now,
        "updated_at": now,
    }
    LIVE_ORDERS[order_id] = order

    payment = await _post_json(
        f"{PAYMENT_SERVICE_URL}/payments/process",
        {
            "order_id": order_id,
            "customer_id": payload.customer_id,
            "restaurant_id": payload.restaurant_id,
            "address": payload.customer.address,
            "amount": totals["total"],
            "currency": totals["currency"],
            "payment_method": payload.payment_method,
        },
    )
    order["payment"] = payment
    order["status"] = "payment_captured"
    order["updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        delivery = await _post_json(
            f"{DELIVERY_SERVICE_URL}/deliveries/allocate",
            {
                "order_id": order_id,
                "restaurant_id": payload.restaurant_id,
                "customer_address": payload.customer.address,
                "customer_location": payload.customer.location,
            },
        )
    except HTTPException as exc:
        if payment and payment.get("id"):
            try:
                refund = await _post_json(
                    f"{PAYMENT_SERVICE_URL}/payments/{payment['id']}/refund",
                    {"reason": "driver_allocation_failed"},
                )
                order["refund"] = refund
            except HTTPException:
                order["refund"] = {"status": "refund_attempt_failed"}
        order["status"] = "delivery_allocation_failed"
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        raise exc

    order["delivery"] = delivery
    order["status"] = "confirmed"
    order["updated_at"] = datetime.now(timezone.utc).isoformat()
    return order


@app.get("/orders/{order_id}", tags=["Orders"])
async def get_order(order_id: str):
    await maybe_database_delay()
    order = LIVE_ORDERS.get(order_id)
    if order:
        if order.get("payment", {}).get("id"):
            try:
                order["payment_status"] = await _get_json(
                    f"{PAYMENT_SERVICE_URL}/payments/{order['payment']['id']}/status"
                )
            except HTTPException:
                order["payment_status"] = {"status": "unavailable"}
        if order.get("delivery"):
            try:
                order["tracking"] = await _get_json(
                    f"{DELIVERY_SERVICE_URL}/deliveries/{order_id}/tracking"
                )
            except HTTPException:
                order["tracking"] = {"status": "unavailable", "progress": 0}
        return order

    seeded = next((item for item in orders() if item["id"] == order_id), None)
    if not seeded:
        raise HTTPException(status_code=404, detail="Order not found")
    return seeded


@app.get("/orders/{order_id}/tracking", tags=["Orders"])
async def get_order_tracking(order_id: str):
    await maybe_database_delay()
    if order_id not in LIVE_ORDERS:
        seeded = next((item for item in orders() if item["id"] == order_id), None)
        if not seeded:
            raise HTTPException(status_code=404, detail="Order not found")
        return {
            "order_id": order_id,
            "status": seeded["status"],
            "progress": seeded.get("progress", 100 if seeded["status"] == "delivered" else 45),
            "eta_minutes": seeded.get("eta_minutes", 0),
            "route": seeded.get("route", []),
        }
    return await _get_json(f"{DELIVERY_SERVICE_URL}/deliveries/{order_id}/tracking")

