from __future__ import annotations

import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", BACKEND_DIR / "data"))

RESTAURANT_SERVICE_URL = os.getenv("RESTAURANT_SERVICE_URL", "http://localhost:8001")
DELIVERY_SERVICE_URL = os.getenv("DELIVERY_SERVICE_URL", "http://localhost:8002")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003")

HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "6.0"))
PAYMENT_TIMEOUT_SECONDS = float(os.getenv("PAYMENT_TIMEOUT_SECONDS", "8.0"))

SERVICE_VERSION = os.getenv("SERVICE_VERSION", "2026.06-demo")

