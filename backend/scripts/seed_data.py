from __future__ import annotations

import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RANDOM = random.Random(42)

NEIGHBORHOODS = [
    "Indiranagar",
    "Koramangala",
    "Whitefield",
    "HSR Layout",
    "Jayanagar",
    "MG Road",
    "Bellandur",
    "JP Nagar",
    "Marathahalli",
    "Hebbal",
]

CUISINES = [
    "Indian",
    "Chinese",
    "Italian",
    "Mexican",
    "American",
    "Thai",
    "Japanese",
    "Mediterranean",
    "Desserts",
    "Healthy",
]

RESTAURANT_PREFIXES = [
    "Urban",
    "Copper",
    "Spice",
    "Velvet",
    "Crisp",
    "Harvest",
    "Midtown",
    "Rocket",
    "Saffron",
    "Oak",
]

RESTAURANT_SUFFIXES = [
    "Kitchen",
    "Bistro",
    "Table",
    "House",
    "Grill",
    "Bowls",
    "Social",
    "Deli",
    "Canteen",
    "Cafe",
]

IMAGE_BY_CATEGORY = {
    "Pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=1200&q=80",
    "Burgers": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=1200&q=80",
    "Biryani": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=1200&q=80",
    "Sushi": "https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?auto=format&fit=crop&w=1200&q=80",
    "Pasta": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=1200&q=80",
    "Noodles": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=1200&q=80",
    "Salads": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=1200&q=80",
    "Tacos": "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?auto=format&fit=crop&w=1200&q=80",
    "Desserts": "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?auto=format&fit=crop&w=1200&q=80",
    "Breakfast": "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?auto=format&fit=crop&w=1200&q=80",
}

MENU_TEMPLATES = {
    "Pizza": [
        ("Margherita Cloud Pizza", "Mozzarella, basil, tomato confit"),
        ("Pepperoni Fire Pizza", "Crisp pepperoni, chili honey, oregano"),
        ("Farmhouse Garden Pizza", "Peppers, onions, olives, corn"),
        ("Truffle Mushroom Pizza", "Mushrooms, parmesan, truffle oil"),
        ("Four Cheese Melt", "Mozzarella, cheddar, gouda, parmesan"),
    ],
    "Burgers": [
        ("Classic Smash Burger", "Double patty, cheddar, house sauce"),
        ("Crispy Chicken Burger", "Spiced fried chicken, slaw, pickles"),
        ("Veggie Stack Burger", "Bean patty, avocado, tomato relish"),
        ("BBQ Bacon Burger", "Smoky sauce, onions, bacon"),
        ("Mushroom Swiss Burger", "Seared mushrooms and swiss cheese"),
    ],
    "Biryani": [
        ("Hyderabadi Dum Biryani", "Aromatic basmati rice and slow cooked masala"),
        ("Paneer Tikka Biryani", "Charred paneer, saffron rice, raita"),
        ("Chicken 65 Biryani", "Crispy chicken bites and spice rice"),
        ("Lucknowi Veg Biryani", "Mild royal spices and vegetables"),
        ("Egg Masala Biryani", "Boiled eggs, onion masala, mint"),
    ],
    "Sushi": [
        ("Salmon Nigiri Set", "Fresh salmon over seasoned rice"),
        ("Spicy Tuna Roll", "Tuna, chili mayo, cucumber"),
        ("Avocado Maki", "Creamy avocado and sesame"),
        ("Tempura Prawn Roll", "Crunchy prawn, eel sauce"),
        ("Rainbow Uramaki", "Assorted fish, avocado, tobiko"),
    ],
    "Pasta": [
        ("Penne Arrabbiata", "Tomato, chili, garlic, parsley"),
        ("Creamy Alfredo Fettuccine", "Parmesan cream and cracked pepper"),
        ("Pesto Gnocchi", "Basil pesto, pine nuts, parmesan"),
        ("Bolognese Rigatoni", "Slow cooked tomato meat sauce"),
        ("Aglio Olio Spaghetti", "Garlic, olive oil, chili flakes"),
    ],
    "Noodles": [
        ("Pad Thai Noodles", "Tamarind, peanuts, bean sprouts"),
        ("Chili Garlic Hakka Noodles", "Wok tossed vegetables and chili"),
        ("Ramen Bowl", "Broth, noodles, egg, scallions"),
        ("Singapore Curry Noodles", "Curry spice, peppers, sprouts"),
        ("Teriyaki Udon", "Udon, teriyaki glaze, sesame"),
    ],
    "Salads": [
        ("Greek Power Salad", "Feta, olives, cucumber, lemon dressing"),
        ("Quinoa Crunch Bowl", "Quinoa, roasted vegetables, seeds"),
        ("Caesar Chicken Salad", "Romaine, parmesan, grilled chicken"),
        ("Thai Peanut Salad", "Cabbage, peanuts, herbs, peanut sauce"),
        ("Avocado Greens Bowl", "Avocado, greens, sprouts, lime"),
    ],
    "Tacos": [
        ("Chipotle Chicken Tacos", "Smoky chicken, salsa, crema"),
        ("Paneer Street Tacos", "Spiced paneer, onions, cilantro"),
        ("Pulled Pork Tacos", "Slow pork, pickled onion"),
        ("Fish Tacos", "Crispy fish, lime slaw"),
        ("Mushroom Corn Tacos", "Mushrooms, corn, jalapeno"),
    ],
    "Desserts": [
        ("Molten Chocolate Cake", "Warm chocolate center and vanilla cream"),
        ("Classic Tiramisu", "Coffee soaked layers and mascarpone"),
        ("Berry Cheesecake", "Cream cheese, berry compote"),
        ("Gulab Jamun Sundae", "Warm jamun and ice cream"),
        ("Mango Panna Cotta", "Silky cream and mango coulis"),
    ],
    "Breakfast": [
        ("Masala Omelette Plate", "Eggs, toast, herbs, chutney"),
        ("Pancake Stack", "Maple syrup, berries, whipped butter"),
        ("Avocado Toast", "Sourdough, avocado, seeds"),
        ("Breakfast Burrito", "Eggs, beans, potatoes, salsa"),
        ("Idli Sambar Box", "Steamed idli, sambar, chutneys"),
    ],
}


def write_json(name: str, data: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / name).write_text(json.dumps(data, indent=2), encoding="utf-8")


def location(index: int) -> dict[str, float]:
    angle = index * 0.65
    radius = 0.018 + (index % 9) * 0.006
    return {
        "lat": round(12.935 + math.sin(angle) * radius + RANDOM.uniform(-0.008, 0.008), 6),
        "lng": round(77.61 + math.cos(angle) * radius + RANDOM.uniform(-0.008, 0.008), 6),
    }


def generate_restaurants() -> list[dict]:
    restaurants: list[dict] = []
    for index in range(1, 101):
        primary = CUISINES[(index - 1) % len(CUISINES)]
        secondary = CUISINES[(index + 3) % len(CUISINES)]
        name = f"{RESTAURANT_PREFIXES[index % len(RESTAURANT_PREFIXES)]} {primary} {RESTAURANT_SUFFIXES[index % len(RESTAURANT_SUFFIXES)]}"
        neighborhood = NEIGHBORHOODS[index % len(NEIGHBORHOODS)]
        rating = round(RANDOM.uniform(3.6, 4.9), 1)
        restaurants.append(
            {
                "id": f"rest_{index:04d}",
                "name": name,
                "slug": name.lower().replace(" ", "-") + f"-{index:04d}",
                "description": f"{primary} favorites from {neighborhood}, built for fast lunches and relaxed dinners.",
                "cuisines": [primary, secondary],
                "neighborhood": neighborhood,
                "rating": rating,
                "review_count": RANDOM.randint(120, 8200),
                "delivery_time_min": RANDOM.randint(18, 48),
                "delivery_fee": round(RANDOM.uniform(0.99, 5.99), 2),
                "min_order": RANDOM.choice([10, 12, 15, 18, 20]),
                "promoted": index % 7 == 0 or rating >= 4.7,
                "open_now": index % 13 != 0,
                "image_url": IMAGE_BY_CATEGORY[list(MENU_TEMPLATES)[index % len(MENU_TEMPLATES)]],
                "location": location(index),
            }
        )
    return restaurants


def generate_menu_items(restaurants: list[dict]) -> list[dict]:
    menu: list[dict] = []
    categories = list(MENU_TEMPLATES)
    for rest_index, restaurant in enumerate(restaurants):
        for item_index in range(5):
            category = categories[(rest_index + item_index) % len(categories)]
            name, description = MENU_TEMPLATES[category][(rest_index + item_index) % 5]
            price = round(RANDOM.uniform(7.5, 22.0), 2)
            menu.append(
                {
                    "id": f"{restaurant['id']}_item_{item_index + 1:02d}",
                    "restaurant_id": restaurant["id"],
                    "name": name,
                    "description": description,
                    "category": category,
                    "price": price,
                    "vegetarian": any(token in name.lower() for token in ["veg", "paneer", "avocado", "salad", "mushroom", "margherita", "idli", "pancake"]),
                    "spice_level": RANDOM.choice(["mild", "medium", "hot"]),
                    "calories": RANDOM.randint(280, 940),
                    "prep_time_min": RANDOM.randint(8, 22),
                    "popularity": RANDOM.randint(55, 99),
                    "available": RANDOM.random() > 0.04,
                    "image_url": IMAGE_BY_CATEGORY[category],
                }
            )
    return menu


def generate_drivers() -> list[dict]:
    vehicles = ["bike", "scooter", "ev-bike"]
    drivers: list[dict] = []
    for index in range(1, 51):
        drivers.append(
            {
                "id": f"drv_{index:04d}",
                "name": f"Driver {index:02d}",
                "phone": f"+91-90000-{index:05d}",
                "vehicle": vehicles[index % len(vehicles)],
                "rating": round(RANDOM.uniform(4.1, 5.0), 1),
                "status": "available" if index % 8 != 0 else RANDOM.choice(["busy", "offline"]),
                "location": location(index + 200),
                "completed_deliveries": RANDOM.randint(50, 2800),
            }
        )
    return drivers


def route_between(start: dict[str, float], end: dict[str, float]) -> list[dict]:
    points: list[dict] = []
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


def generate_orders(restaurants: list[dict], menu_items: list[dict]) -> list[dict]:
    menu_by_restaurant: dict[str, list[dict]] = {}
    for item in menu_items:
        menu_by_restaurant.setdefault(item["restaurant_id"], []).append(item)

    statuses = ["delivered", "delivered", "delivered", "cancelled", "preparing", "picked_up"]
    orders: list[dict] = []
    now = datetime.now(timezone.utc)
    for index in range(1, 1001):
        restaurant = RANDOM.choice(restaurants)
        items = RANDOM.sample(menu_by_restaurant[restaurant["id"]], RANDOM.randint(1, 3))
        order_items = []
        subtotal = 0.0
        for item in items:
            quantity = RANDOM.randint(1, 3)
            line_total = round(item["price"] * quantity, 2)
            subtotal += line_total
            order_items.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "quantity": quantity,
                    "price": item["price"],
                    "line_total": line_total,
                }
            )
        customer_location = location(index + 500)
        tax = round((subtotal + restaurant["delivery_fee"] + 1.99) * 0.0825, 2)
        total = round(subtotal + restaurant["delivery_fee"] + 1.99 + tax, 2)
        status = RANDOM.choice(statuses)
        created_at = now - timedelta(days=RANDOM.randint(0, 29), minutes=RANDOM.randint(0, 1440))
        orders.append(
            {
                "id": f"seed_ord_{index:04d}",
                "customer_id": f"user_{RANDOM.randint(1, 80):03d}",
                "restaurant_id": restaurant["id"],
                "restaurant_name": restaurant["name"],
                "items": order_items,
                "status": status,
                "progress": 100 if status == "delivered" else RANDOM.randint(18, 82),
                "eta_minutes": 0 if status == "delivered" else RANDOM.randint(8, 34),
                "totals": {
                    "subtotal": round(subtotal, 2),
                    "delivery_fee": restaurant["delivery_fee"],
                    "platform_fee": 1.99,
                    "tax": tax,
                    "total": total,
                    "currency": "USD",
                },
                "payment_status": "captured" if status != "cancelled" else "refunded",
                "route": route_between(restaurant["location"], customer_location),
                "created_at": created_at.isoformat(),
            }
        )
    return orders


def main() -> None:
    restaurants = generate_restaurants()
    menu = generate_menu_items(restaurants)
    drivers = generate_drivers()
    orders = generate_orders(restaurants, menu)
    write_json("restaurants.json", restaurants)
    write_json("menu_items.json", menu)
    write_json("drivers.json", drivers)
    write_json("orders.json", orders)
    print(
        f"Generated {len(restaurants)} restaurants, {len(menu)} menu items, "
        f"{len(drivers)} drivers, and {len(orders)} orders in {DATA_DIR}"
    )


if __name__ == "__main__":
    main()

