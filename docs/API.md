# API Documentation

All services expose interactive FastAPI docs at `/docs`.

## Restaurant Service

Base URL: `http://localhost:8001`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Service health |
| `GET` | `/feature-flags` | Current behavior flags |
| `PATCH` | `/feature-flags` | Toggle behavior flags |
| `GET` | `/restaurants` | List restaurants with `q`, `category`, `cuisine`, `min_rating`, `max_delivery_fee`, `sort_by`, `page`, `limit` |
| `GET` | `/restaurants/{restaurant_id}` | Restaurant details |
| `GET` | `/restaurants/{restaurant_id}/menu` | Menu listing with `q`, `category`, `vegetarian` |
| `GET` | `/search/restaurants?q=...` | Search restaurants |
| `GET` | `/search/menu?q=...` | Search food items |
| `GET` | `/categories` | Food categories and cuisines |
| `GET` | `/recommendations` | Recommended restaurants |
| `POST` | `/orders` | Price cart, process payment, allocate driver |
| `GET` | `/orders/{order_id}` | Order details plus payment and delivery state |
| `GET` | `/orders/{order_id}/tracking` | Proxied delivery tracking |

### Create Order

```json
{
  "restaurant_id": "rest_0001",
  "customer_id": "user_demo_001",
  "customer": {
    "name": "Ananya Rao",
    "phone": "+91 98765 43210",
    "address": "221B Market Street, Koramangala, Bengaluru"
  },
  "items": [
    { "menu_item_id": "rest_0001_item_01", "quantity": 2 }
  ],
  "payment_method": "card",
  "coupon_code": "DEMO20"
}
```

## Delivery Service

Base URL: `http://localhost:8002`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/drivers` | Driver listing, optional `status` |
| `POST` | `/deliveries/allocate` | Allocate nearest available driver |
| `GET` | `/deliveries/{order_id}/tracking` | Status, progress, ETA, route |
| `PATCH` | `/deliveries/{order_id}/status` | Manually update delivery status |
| `GET` | `/deliveries/{order_id}/route` | Route points |
| `POST` | `/eta` | ETA calculation |

## Payment Service

Base URL: `http://localhost:8003`

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/fraud/validate` | Fraud validation |
| `POST` | `/payments/process` | Process payment |
| `GET` | `/payments/{payment_id}/status` | Payment status |
| `GET` | `/payments/order/{order_id}/status` | Payment status by order |
| `POST` | `/payments/{payment_id}/refund` | Refund simulation |

## Feature Flags

Flags can be set through environment variables or toggled at runtime with `PATCH /feature-flags`.

```json
{
  "slow_recommendation_service": true,
  "payment_timeout": false,
  "driver_allocation_failure": false,
  "random_api_failures": false,
  "database_query_delay": true
}
```

Environment variable names:

| Flag | Environment variable | Services |
| --- | --- | --- |
| Slow Recommendation Service | `SLOW_RECOMMENDATION_SERVICE` | Restaurant |
| Payment Timeout | `PAYMENT_TIMEOUT` | Payment |
| Driver Allocation Failure | `DRIVER_ALLOCATION_FAILURE` | Delivery |
| Random API Failures | `RANDOM_API_FAILURES` | All |
| Database Query Delay | `DATABASE_QUERY_DELAY` | All |

