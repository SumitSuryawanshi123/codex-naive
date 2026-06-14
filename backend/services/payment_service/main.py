from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from common.api import configure_app
from common.feature_flags import maybe_database_delay, maybe_payment_timeout


app = FastAPI(
    title="Food Delivery Payment Service",
    description="Payment processing, payment status, refunds, and fraud validation.",
    version="1.0.0",
)
configure_app(app, "payment-service")

PAYMENTS: dict[str, dict] = {}


class FraudRequest(BaseModel):
    order_id: str
    customer_id: str = "guest"
    amount: float = Field(gt=0)
    payment_method: Literal["card", "upi", "wallet", "cash"] = "card"
    restaurant_id: str | None = None
    address: str | None = None


class PaymentRequest(FraudRequest):
    currency: str = "USD"
    card_last4: str | None = None


class RefundRequest(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    reason: str = "customer_requested"


def _risk_score(payload: FraudRequest) -> float:
    score = 0.08
    if payload.amount > 85:
        score += 0.23
    if payload.payment_method == "cash":
        score += 0.12
    if payload.address and len(payload.address.strip()) < 12:
        score += 0.14
    score += random.uniform(0.0, 0.18)
    return round(min(score, 0.97), 2)


@app.post("/fraud/validate", tags=["Fraud"])
async def validate_fraud(payload: FraudRequest):
    await maybe_database_delay()
    score = _risk_score(payload)
    decision = "review" if score >= 0.68 else "approved"
    if score >= 0.84:
        decision = "blocked"
    return {
        "order_id": payload.order_id,
        "decision": decision,
        "risk_score": score,
        "signals": {
            "high_value_order": payload.amount > 85,
            "short_address": bool(payload.address and len(payload.address.strip()) < 12),
            "cash_payment": payload.payment_method == "cash",
        },
    }


@app.post("/payments/process", tags=["Payments"])
async def process_payment(payload: PaymentRequest):
    await maybe_payment_timeout()
    await maybe_database_delay()
    fraud = await validate_fraud(payload)
    if fraud["decision"] == "blocked":
        raise HTTPException(status_code=402, detail="Payment blocked by fraud validation")

    payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    success_rate = 0.96 if payload.payment_method != "cash" else 0.99
    status = "captured" if random.random() < success_rate else "failed"
    payment = {
        "id": payment_id,
        "order_id": payload.order_id,
        "status": status,
        "amount": round(payload.amount, 2),
        "currency": payload.currency,
        "method": payload.payment_method,
        "fraud": fraud,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "refunds": [],
    }
    PAYMENTS[payment_id] = payment
    if status == "failed":
        raise HTTPException(status_code=402, detail="Payment authorization failed")
    return payment


@app.get("/payments/{payment_id}/status", tags=["Payments"])
async def payment_status(payment_id: str):
    await maybe_database_delay()
    payment = PAYMENTS.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {
        "id": payment["id"],
        "order_id": payment["order_id"],
        "status": payment["status"],
        "amount": payment["amount"],
        "currency": payment["currency"],
        "refunds": payment["refunds"],
        "updated_at": payment["updated_at"],
    }


@app.get("/payments/order/{order_id}/status", tags=["Payments"])
async def payment_status_by_order(order_id: str):
    await maybe_database_delay()
    payment = next((item for item in PAYMENTS.values() if item["order_id"] == order_id), None)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return await payment_status(payment["id"])


@app.post("/payments/{payment_id}/refund", tags=["Payments"])
async def refund_payment(payment_id: str, payload: RefundRequest):
    await maybe_database_delay()
    payment = PAYMENTS.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment["status"] not in {"captured", "partially_refunded"}:
        raise HTTPException(status_code=409, detail="Payment is not refundable")
    amount = round(payload.amount or payment["amount"], 2)
    refund = {
        "id": f"rfnd_{uuid.uuid4().hex[:12]}",
        "amount": amount,
        "status": "succeeded",
        "reason": payload.reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    payment["refunds"].append(refund)
    refunded_total = round(sum(item["amount"] for item in payment["refunds"]), 2)
    payment["status"] = "refunded" if refunded_total >= payment["amount"] else "partially_refunded"
    payment["updated_at"] = datetime.now(timezone.utc).isoformat()
    return {"payment": payment, "refund": refund}

