"""Command-line interface for the provider app."""

import argparse
import json
from pathlib import Path
import httpx
import uvicorn

def list_catalog(api_url: str) -> None:
    url = api_url.rstrip("/") + "/catalog"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        items = response.json()
    for item in items:
        product = item["product"]
        print(f"Product: {product['name']} ({product['description']})")
        print(f"  Lead time: {product['lead_time_days']} days")
        for tier in item["pricing_tiers"]:
            print(f"  Qty {tier['min_quantity']}+: ${tier['price']:.2f}")
        print()

def list_stock(api_url: str) -> None:
    url = api_url.rstrip("/") + "/stock"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        stocks = response.json()
    for s in stocks:
        print(f"Product {s['product_id']}: {s['quantity']} units")

def list_orders(api_url: str, status: str | None) -> None:
    url = api_url.rstrip("/") + "/orders"
    params = {}
    if status:
        params["status"] = status
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        orders = response.json()
    for order in orders:
        print(f"Order {order['id']}: Product {order['product_id']}, Qty {order['quantity']}, Status {order['status']}, Expected {order['expected_delivery_day']}")

def show_order(api_url: str, order_id: int) -> None:
    url = api_url.rstrip("/") + f"/orders/{order_id}"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        if response.status_code == 404:
            print("Order not found")
            return
        response.raise_for_status()
        order = response.json()
    print(f"Order {order['id']}:")
    print(f"  Product: {order['product_id']}")
    print(f"  Quantity: {order['quantity']}")
    print(f"  Status: {order['status']}")
    print(f"  Placed: {order.get('placed_at')}")
    print(f"  Expected delivery: Day {order['expected_delivery_day']}")
    print(f"  Total price: ${order['total_price']:.2f}")

def set_price(api_url: str, product: int, tier: int, price: float) -> None:
    url = api_url.rstrip("/") + f"/catalog/{product}/price"
    params = {"min_quantity": tier, "price": price}
    with httpx.Client(timeout=10.0) as client:
        response = client.put(url, params=params)
        response.raise_for_status()
    print(f"Set price for product {product}, qty {tier}+ to ${price:.2f}")

def restock_cmd(api_url: str, product: int, quantity: float) -> None:
    url = api_url.rstrip("/") + "/stock/restock"
    params = {"product_id": product, "quantity": quantity}
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, params=params)
        response.raise_for_status()
    print(f"Added {quantity} units to product {product}")

def day_advance(api_url: str) -> None:
    url = api_url.rstrip("/") + "/day/advance"
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url)
        response.raise_for_status()
        result = response.json()
    print(f"Advanced to day {result}")

def day_current(api_url: str) -> None:
    url = api_url.rstrip("/") + "/day/current"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        result = response.json()
    print(f"Current day: {result['current_day']}")

def export_state(api_url: str) -> None:
    url = api_url.rstrip("/") + "/export"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))

def import_state(api_url: str, file_path: str) -> None:
    url = api_url.rstrip("/") + "/import"
    with open(file_path, "rb") as in_file:
        files = {"file": (Path(file_path).name, in_file, "application/json")}
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, files=files)
            response.raise_for_status()
    print("State imported.")

def serve_app(port: int) -> None:
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)

def init_db() -> None:
    from src.database import engine, SessionLocal
    from src.models import Base
    from src.services.seed import seed_database_from_config
    from src.config import Settings
    settings = Settings()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database_from_config(session, settings.default_seed_path)
    print("Database initialized and seeded.")

def main() -> None:
    parser = argparse.ArgumentParser(description="3D Printer Provider Simulator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_api_url(p):
        p.add_argument("--api-url", type=str, default="http://localhost:8001/api", help="API URL")

    p = subparsers.add_parser("catalog", help="List the product catalog")
    add_api_url(p)

    p = subparsers.add_parser("stock", help="Show current inventory")
    add_api_url(p)

    orders_parser = subparsers.add_parser("orders", help="Manage orders")
    orders_sub = orders_parser.add_subparsers(dest="orders_command", required=True)
    list_parser = orders_sub.add_parser("list", help="List all orders")
    list_parser.add_argument("--status", type=str, help="Filter by status")
    add_api_url(list_parser)
    show_parser = orders_sub.add_parser("show", help="Show details of a specific order")
    show_parser.add_argument("order_id", type=int)
    add_api_url(show_parser)

    price_parser = subparsers.add_parser("price", help="Manage pricing")
    price_sub = price_parser.add_subparsers(dest="price_command", required=True)
    set_parser = price_sub.add_parser("set", help="Set pricing tier for a product")
    set_parser.add_argument("product", type=int)
    set_parser.add_argument("tier", type=int)
    set_parser.add_argument("price", type=float)
    add_api_url(set_parser)

    restock_parser = subparsers.add_parser("restock", help="Add stock to a product")
    restock_parser.add_argument("product", type=int)
    restock_parser.add_argument("quantity", type=float)
    add_api_url(restock_parser)

    day_parser = subparsers.add_parser("day", help="Manage simulation day")
    day_sub = day_parser.add_subparsers(dest="day_command", required=True)
    p = day_sub.add_parser("advance", help="Advance the simulation by one day")
    add_api_url(p)
    p = day_sub.add_parser("current", help="Show the current simulation day")
    add_api_url(p)

    p = subparsers.add_parser("export", help="Export state to JSON")
    add_api_url(p)

    import_parser = subparsers.add_parser("import", help="Import state from JSON file")
    import_parser.add_argument("file", help="JSON file to import")
    add_api_url(import_parser)

    serve_parser = subparsers.add_parser("serve", help="Start the FastAPI server")
    serve_parser.add_argument("--port", type=int, default=8001)

    subparsers.add_parser("init_db", help="Initialize the database and seed with data")

    args = parser.parse_args()

    try:
        if args.command == "catalog":
            list_catalog(args.api_url)
        elif args.command == "stock":
            list_stock(args.api_url)
        elif args.command == "orders":
            if args.orders_command == "list":
                list_orders(args.api_url, getattr(args, 'status', None))
            elif args.orders_command == "show":
                show_order(args.api_url, args.order_id)
        elif args.command == "price":
            if args.price_command == "set":
                set_price(args.api_url, args.product, args.tier, args.price)
        elif args.command == "restock":
            restock_cmd(args.api_url, args.product, args.quantity)
        elif args.command == "day":
            if args.day_command == "advance":
                day_advance(args.api_url)
            elif args.day_command == "current":
                day_current(args.api_url)
        elif args.command == "export":
            export_state(args.api_url)
        elif args.command == "import":
            import_state(args.api_url, args.file)
        elif args.command == "serve":
            serve_app(args.port)
        elif args.command == "init_db":
            init_db()
    except httpx.HTTPError as exc:
        print(f"API request failed: {exc}")

if __name__ == "__main__":
    main()