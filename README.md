# CraveCart Food Delivery Demo

CraveCart is a production-style food delivery demo with a React storefront and three FastAPI microservices. The browser talks to the Restaurant Service, and checkout creates service-to-service calls into Payment and Delivery.

No tracing, telemetry, monitoring, analytics, logging pipeline, OpenTelemetry setup, AI debugging, or visualization layer is implemented. The app is intentionally clean so a platform SDK can be integrated later.

## Architecture

```text
React + Vite frontend
        |
        v
Restaurant Service :8001
        |
        +--> Payment Service :8003
        |
        +--> Delivery Service :8002
```

## What Is Included

- React, Vite, TailwindCSS, React Router, Axios, Framer Motion
- FastAPI services for restaurant discovery, delivery, and payment
- 100 generated restaurants
- 500 generated menu items
- 50 generated drivers
- 1000 generated mock orders
- Docker Compose for all services
- Runtime feature flags for realistic business failures and latency
- API docs in [docs/API.md](docs/API.md)

## Run With Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Frontend: `http://localhost:5173`
- Restaurant API docs: `http://localhost:8001/docs`
- Delivery API docs: `http://localhost:8002/docs`
- Payment API docs: `http://localhost:8003/docs`

## Run Locally

Backend:

```bash
python backend/scripts/seed_data.py
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt

$env:PYTHONPATH="backend"
uvicorn services.payment_service.main:app --host 0.0.0.0 --port 8003
uvicorn services.delivery_service.main:app --host 0.0.0.0 --port 8002
$env:DELIVERY_SERVICE_URL="http://localhost:8002"
$env:PAYMENT_SERVICE_URL="http://localhost:8003"
uvicorn services.restaurant_service.main:app --host 0.0.0.0 --port 8001
```

Frontend:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Feature Flags

Use `.env`, Compose environment variables, or `PATCH /feature-flags`.

```bash
curl -X PATCH http://localhost:8001/feature-flags ^
  -H "Content-Type: application/json" ^
  -d "{\"slow_recommendation_service\":true,\"database_query_delay\":true}"
```

Available flags:

- `SLOW_RECOMMENDATION_SERVICE`
- `PAYMENT_TIMEOUT`
- `DRIVER_ALLOCATION_FAILURE`
- `RANDOM_API_FAILURES`
- `DATABASE_QUERY_DELAY`

## Service Interaction During Checkout

1. Frontend posts cart and address to `POST /orders` on Restaurant Service.
2. Restaurant Service validates menu items and calculates subtotal, fees, tax, discount, and total.
3. Restaurant Service calls Payment Service to run fraud validation and capture payment.
4. Restaurant Service calls Delivery Service to allocate the nearest available driver and generate route/ETA.
5. Frontend redirects to order tracking and polls the Restaurant Service tracking proxy.

If driver allocation fails after payment capture, the Restaurant Service attempts a refund simulation before returning the failure.

## Regenerate Seed Data

```bash
python backend/scripts/seed_data.py
```

Generated JSON files live in `backend/data`.

