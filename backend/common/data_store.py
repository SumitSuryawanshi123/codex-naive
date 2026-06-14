from __future__ import annotations

import json
import math
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

from common.config import DATA_DIR


def _load_json(name: str) -> list[dict[str, Any]]:
    path = Path(DATA_DIR) / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing seed file {path}. Run `python backend/scripts/seed_data.py`."
        )
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def restaurants() -> list[dict[str, Any]]:
    return _load_json("restaurants.json")


@lru_cache(maxsize=1)
def menu_items() -> list[dict[str, Any]]:
    return _load_json("menu_items.json")


@lru_cache(maxsize=1)
def drivers() -> list[dict[str, Any]]:
    return _load_json("drivers.json")


@lru_cache(maxsize=1)
def orders() -> list[dict[str, Any]]:
    return _load_json("orders.json")


def get_restaurant(restaurant_id: str) -> dict[str, Any] | None:
    return next((item for item in restaurants() if item["id"] == restaurant_id), None)


def get_menu_item(menu_item_id: str) -> dict[str, Any] | None:
    return next((item for item in menu_items() if item["id"] == menu_item_id), None)


def menu_for_restaurant(restaurant_id: str) -> list[dict[str, Any]]:
    return [item for item in menu_items() if item["restaurant_id"] == restaurant_id]


def categories() -> list[str]:
    return sorted({item["category"] for item in menu_items()})


def cuisines() -> list[str]:
    seen: set[str] = set()
    for restaurant in restaurants():
        seen.update(restaurant["cuisines"])
    return sorted(seen)


def haversine_km(a: dict[str, float], b: dict[str, float]) -> float:
    radius_km = 6371.0
    lat1 = math.radians(a["lat"])
    lon1 = math.radians(a["lng"])
    lat2 = math.radians(b["lat"])
    lon2 = math.radians(b["lng"])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    value = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return round(radius_km * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value)), 2)


def address_to_location(address: str) -> dict[str, float]:
    seed = sum(ord(ch) for ch in address)
    randomizer = random.Random(seed)
    return {
        "lat": round(12.935 + randomizer.uniform(-0.055, 0.06), 6),
        "lng": round(77.61 + randomizer.uniform(-0.075, 0.075), 6),
    }


def route_between(start: dict[str, float], end: dict[str, float]) -> list[dict[str, float | str]]:
    points: list[dict[str, float | str]] = []
    for index, label in enumerate(["Restaurant", "Pickup lane", "Main road", "Drop-off lane", "Customer"]):
        ratio = index / 4
        bend = math.sin(ratio * math.pi) * 0.006
        points.append(
            {
                "lat": round(start["lat"] + (end["lat"] - start["lat"]) * ratio + bend, 6),
                "lng": round(start["lng"] + (end["lng"] - start["lng"]) * ratio - bend, 6),
                "label": label,
            }
        )
    return points

