from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def money(value: float | Decimal) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def price_order(
    restaurant: dict[str, Any],
    selected_items: list[dict[str, Any]],
    coupon_code: str | None = None,
) -> dict[str, Any]:
    subtotal = sum(item["price"] * item["quantity"] for item in selected_items)
    discount = 0.0
    coupon = (coupon_code or "").strip().upper()
    if coupon == "WELCOME50":
        discount = min(subtotal * 0.5, 12.0)
    elif coupon == "DEMO20":
        discount = subtotal * 0.2

    platform_fee = 1.99
    delivery_fee = 0 if subtotal > 35 else restaurant["delivery_fee"]
    tax = (subtotal - discount + platform_fee + delivery_fee) * 0.0825
    total = max(0, subtotal - discount + platform_fee + delivery_fee + tax)
    return {
        "subtotal": money(subtotal),
        "discount": money(discount),
        "platform_fee": money(platform_fee),
        "delivery_fee": money(delivery_fee),
        "tax": money(tax),
        "total": money(total),
        "currency": "USD",
    }

