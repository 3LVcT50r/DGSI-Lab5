import argparse
import json
import os
from pathlib import Path

import uvicorn
from sqlalchemy.orm import Session

from src.config import Settings
from src.database import SessionLocal, engine
from src.models import Base
from src.services.seed import seed_database_from_config
from src.services.retailer import (
    get_catalog,
    get_stock,
    get_customer_orders,
    get_customer_order,
    create_customer_order,
    fulfill_order,
    backorder_order,
    get_purchase_orders,
    get_purchase_order,
    create_purchase_order,
    get_current_day,
    advance_day,
    export_state,
    import_state,
    set_price,
)
from src.schemas.request import CustomerOrderCreate, PurchaseCreate, PriceUpdate


def load_settings(config_path: str | None = None) -> Settings:
    if config_path:
        os.environ["DEFAULT_CONFIG_PATH"] = config_path
    return Settings()


def _with_session(func):
    def wrapper(*args, **kwargs):
        with SessionLocal() as session:
            return func(session, *args, **kwargs)
    return wrapper


@_with_session
def catalog(session: Session):
    items = get_catalog(session)
    for item in items:
        print(f"Product {item.id}: {item.name} - {item.description}")
        print(f"  Wholesale: ${item.manufacturer_price:.2f}, Retail: ${item.retail_price:.2f}\n")


@_with_session
def stock(session: Session):
    items = get_stock(session)
    for item in items:
        print(
            f"Product {item.product_id}: available={item.quantity_available}, on_hold={item.quantity_on_hold}"
        )


@_with_session
def customers_orders(session: Session, status: str | None = None):
    orders = get_customer_orders(session, status)
    for order in orders:
        print(
            f"Order {order.id}: {order.customer_name}, product={order.product_id}, qty={order.quantity}, status={order.status}, created_day={order.created_day}"
        )


@_with_session
def customers_order(session: Session, order_id: int):
    order = get_customer_order(session, order_id)
    if not order:
        print("Order not found")
        return
    print(json.dumps(order.model_dump(), indent=2, default=str))


@_with_session
def fulfill(session: Session, order_id: int):
    try:
        order = fulfill_order(session, order_id)
        print(f"Fulfilled order {order.id} (status={order.status})")
    except ValueError as exc:
        print(f"Error: {exc}")


@_with_session
def backorder(session: Session, order_id: int):
    try:
        order = backorder_order(session, order_id)
        print(f"Backordered order {order.id} (status={order.status})")
    except ValueError as exc:
        print(f"Error: {exc}")


@_with_session
def purchase_list(session: Session, status: str | None = None):
    orders = get_purchase_orders(session, status)
    for order in orders:
        print(
            f"PO {order.id}: product={order.product_id}, qty={order.quantity}, status={order.status}, expected_day={order.expected_delivery_day}"
        )


@_with_session
def purchase_create(session: Session, settings: Settings, product: str, quantity: int):
    payload = {}
    try:
        payload["product_id"] = int(product)
    except ValueError:
        payload["product_name"] = product
    payload["quantity"] = quantity
    try:
        order = create_purchase_order(session, settings, PurchaseCreate(**payload))
        print(f"Created purchase order {order.id} for manufacturer order {order.manufacturer_order_id}")
    except ValueError as exc:
        print(f"Error: {exc}")


@_with_session
def price_list_cmd(session: Session):
    items = get_catalog(session)
    for item in items:
        print(f"{item.name}: wholesale=${item.manufacturer_price:.2f}, retail=${item.retail_price:.2f}")


@_with_session
def set_price_cmd(session: Session, product: str, price: float):
    payload = {}
    try:
        payload["product_id"] = int(product)
    except ValueError:
        payload["product_name"] = product
    payload["price"] = price
    try:
        product_data = set_price(session, PriceUpdate(**payload))
        print(f"Updated retail price for {product_data.name} to ${product_data.retail_price:.2f}")
    except ValueError as exc:
        print(f"Error: {exc}")


@_with_session
def day_advance(session: Session, settings: Settings):
    new_day = advance_day(session, settings)
    print(f"Advanced to day {new_day}")


@_with_session
def day_current(session: Session):
    current = get_current_day(session)
    print(f"Current day: {current}")


@_with_session
def export_cmd(session: Session):
    data = export_state(session)
    print(data)


@_with_session
def import_cmd(session: Session, file_path: str):
    with open(file_path, "r", encoding="utf-8") as input_file:
        payload = json.load(input_file)
    import_state(session, json.dumps(payload))
    print("Imported state successfully.")


def init_db(settings: Settings):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database_from_config(session, settings.default_seed_path)
    print("Database initialized and seeded.")


def serve(settings: Settings, port: int):
    if settings.default_config_path.exists():
        os.environ["DEFAULT_CONFIG_PATH"] = str(settings.default_config_path)
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="3D Printer Retailer Simulator CLI")
    parser.add_argument("--config", type=str, help="Override config file path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("catalog", help="List the product catalog")
    subparsers.add_parser("stock", help="Show current stock")

    customers_parser = subparsers.add_parser("customers", help="Customer order commands")
    customers_sub = customers_parser.add_subparsers(dest="subcommand", required=True)
    orders_parser = customers_sub.add_parser("orders", help="List customer orders")
    orders_parser.add_argument("--status", type=str, help="Filter by status")
    order_parser = customers_sub.add_parser("order", help="Show a specific order")
    order_parser.add_argument("order_id", type=int)

    subparsers.add_parser("fulfill", help="Fulfill a customer order").add_argument("order_id", type=int)
    subparsers.add_parser("backorder", help="Backorder a customer order").add_argument("order_id", type=int)

    purchase_parser = subparsers.add_parser("purchase", help="Purchase order commands")
    purchase_sub = purchase_parser.add_subparsers(dest="subcommand", required=True)
    purchase_sub.add_parser("list", help="List purchase orders")
    purchase_create_parser = purchase_sub.add_parser("create", help="Create a purchase order")
    purchase_create_parser.add_argument("model", type=str)
    purchase_create_parser.add_argument("qty", type=int)

    price_parser = subparsers.add_parser("price", help="Retail pricing commands")
    price_sub = price_parser.add_subparsers(dest="price_command", required=True)
    price_sub.add_parser("list", help="List retail prices for all products")
    price_set_parser = price_sub.add_parser("set", help="Set retail price for a product")
    price_set_parser.add_argument("model", type=str)
    price_set_parser.add_argument("price", type=float)

    day_parser = subparsers.add_parser("day", help="Manage simulation day")
    day_sub = day_parser.add_subparsers(dest="day_command", required=True)
    day_sub.add_parser("advance", help="Advance a simulated day")
    day_sub.add_parser("current", help="Show current simulated day")

    subparsers.add_parser("export", help="Export state to JSON")
    import_parser = subparsers.add_parser("import", help="Import state from JSON file")
    import_parser.add_argument("file", help="JSON file path")

    serve_parser = subparsers.add_parser("serve", help="Start the FastAPI server")
    serve_parser.add_argument("--port", type=int, default=8003)

    subparsers.add_parser("init_db", help="Initialize the database and seed data")

    args = parser.parse_args()
    settings = load_settings(args.config)

    if args.command == "catalog":
        catalog()
    elif args.command == "stock":
        stock()
    elif args.command == "customers":
        if args.subcommand == "orders":
            customers_orders(args.status)
        elif args.subcommand == "order":
            customers_order(args.order_id)
    elif args.command == "fulfill":
        fulfill(args.order_id)
    elif args.command == "backorder":
        backorder(args.order_id)
    elif args.command == "purchase":
        if args.subcommand == "list":
            purchase_list(args.status if hasattr(args, "status") else None)
        elif args.subcommand == "create":
            purchase_create(settings, args.model, args.qty)
    elif args.command == "price":
        if args.price_command == "list":
            price_list_cmd()
        elif args.price_command == "set":
            set_price_cmd(args.model, args.price)
    elif args.command == "day":
        if args.day_command == "advance":
            day_advance(settings)
        elif args.day_command == "current":
            day_current()
    elif args.command == "export":
        export_cmd()
    elif args.command == "import":
        import_cmd(args.file)
    elif args.command == "serve":
        serve(settings, args.port)
    elif args.command == "init_db":
        init_db(settings)


if __name__ == "__main__":
    main()
