"""Command-line interface for the provider app."""

import argparse
from pathlib import Path
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base
from .services.seed import seed_database_from_config
from .services.provider import (
    get_catalog, get_stock, get_orders, get_order,
    place_order, advance_day, get_current_day,
    set_price, restock, export_state, import_state
)
from .schemas.request import OrderCreate
from .config import Settings

class _TyperStub:
    def Typer(self):
        return self

    def command(self):
        def decorator(func):
            return func
        return decorator

    def callback(self):
        def decorator(func):
            return func
        return decorator

    def __call__(self) -> None:
        parser = argparse.ArgumentParser(description="3D Printer Provider Simulator CLI")
        subparsers = parser.add_subparsers(dest="command", required=True)

        # catalog
        subparsers.add_parser("catalog", help="List the product catalog")

        # stock
        subparsers.add_parser("stock", help="Show current inventory")

        # orders
        orders_parser = subparsers.add_parser("orders", help="Manage orders")
        orders_sub = orders_parser.add_subparsers(dest="orders_command", required=True)
        list_parser = orders_sub.add_parser("list", help="List all orders")
        list_parser.add_argument("--status", type=str, help="Filter by status")
        show_parser = orders_sub.add_parser("show", help="Show details of a specific order")
        show_parser.add_argument("order_id", type=int)

        # price
        price_parser = subparsers.add_parser("price", help="Manage pricing")
        price_sub = price_parser.add_subparsers(dest="price_command", required=True)
        set_parser = price_sub.add_parser("set", help="Set pricing tier for a product")
        set_parser.add_argument("product", type=int)
        set_parser.add_argument("tier", type=int)
        set_parser.add_argument("price", type=float)

        # restock
        restock_parser = subparsers.add_parser("restock", help="Add stock to a product")
        restock_parser.add_argument("product", type=int)
        restock_parser.add_argument("quantity", type=float)

        # day
        day_parser = subparsers.add_parser("day", help="Manage simulation day")
        day_sub = day_parser.add_subparsers(dest="day_command", required=True)
        day_sub.add_parser("advance", help="Advance the simulation by one day")
        day_sub.add_parser("current", help="Show the current simulation day")

        # export
        subparsers.add_parser("export", help="Export state to JSON")

        # import
        import_parser = subparsers.add_parser("import", help="Import state from JSON file")
        import_parser.add_argument("file", help="JSON file to import")

        # serve
        serve_parser = subparsers.add_parser("serve", help="Start the FastAPI server")
        serve_parser.add_argument("--port", type=int, default=8001)

        # init_db
        subparsers.add_parser("init_db", help="Initialize the database and seed with data")

        args = parser.parse_args()

        if args.command == "catalog":
            catalog()
        elif args.command == "stock":
            stock()
        elif args.command == "orders":
            if args.orders_command == "list":
                orders(getattr(args, 'status', None))
            elif args.orders_command == "show":
                order_show(args.order_id)
        elif args.command == "price":
            if args.price_command == "set":
                price_set(args.product, args.tier, args.price)
        elif args.command == "restock":
            restock_cmd(args.product, args.quantity)
        elif args.command == "day":
            if args.day_command == "advance":
                day_advance()
            elif args.day_command == "current":
                day_current()
        elif args.command == "export":
            export()
        elif args.command == "import":
            import_cmd(args.file)
        elif args.command == "serve":
            serve(args.port)
        elif args.command == "init_db":
            init_db()

    @staticmethod
    def echo(message: str = "") -> None:
        print(message)

    @staticmethod
    def Option(default=None, help: str = ""):
        return default


typer = _TyperStub()
app = typer.Typer()
settings = Settings()


@app.callback()
def callback():
    """3D Printer Provider Simulator CLI"""
    pass


@app.command()
def catalog():
    """List the product catalog."""
    with SessionLocal() as session:
        items = get_catalog(session)
        for item in items:
            typer.echo(f"Product: {item.product.name} ({item.product.description})")
            typer.echo(f"  Lead time: {item.product.lead_time_days} days")
            for tier in item.pricing_tiers:
                typer.echo(f"  Qty {tier.min_quantity}+: ${tier.price:.2f}")
            typer.echo()


@app.command()
def stock():
    """List current stock levels."""
    with SessionLocal() as session:
        stocks = get_stock(session)
        for s in stocks:
            typer.echo(f"Product {s.product_id}: {s.quantity} units")


@app.command()
def orders(status: str = typer.Option(None, help="Filter by status")):
    """List orders."""
    with SessionLocal() as session:
        orders_list = get_orders(session, status)
        for order in orders_list:
            typer.echo(f"Order {order.id}: Product {order.product_id}, Qty {order.quantity}, Status {order.status}, Expected {order.expected_delivery_day}")


@app.command()
def order_show(order_id: int):
    """Show details of a specific order."""
    with SessionLocal() as session:
        order = get_order(session, order_id)
        if order:
            typer.echo(f"Order {order.id}:")
            typer.echo(f"  Product: {order.product_id}")
            typer.echo(f"  Quantity: {order.quantity}")
            typer.echo(f"  Status: {order.status}")
            typer.echo(f"  Placed: {order.placed_at}")
            typer.echo(f"  Expected delivery: Day {order.expected_delivery_day}")
            typer.echo(f"  Total price: ${order.total_price:.2f}")
        else:
            typer.echo("Order not found")


@app.command()
def price_set(product: int, tier: int, price: float):
    """Set pricing tier for a product."""
    with SessionLocal() as session:
        set_price(session, product, tier, price)
        typer.echo(f"Set price for product {product}, qty {tier}+ to ${price:.2f}")


@app.command()
def restock_cmd(product: int, quantity: float):
    """Add stock to a product."""
    with SessionLocal() as session:
        restock(session, product, quantity)
        typer.echo(f"Added {quantity} units to product {product}")


@app.command()
def day_advance():
    """Advance the simulation by one day."""
    with SessionLocal() as session:
        new_day = advance_day(session)
        typer.echo(f"Advanced to day {new_day}")


@app.command()
def day_current():
    """Show the current simulated day."""
    with SessionLocal() as session:
        current = get_current_day(session)
        typer.echo(f"Current day: {current}")


@app.command()
def serve(port: int = 8001):
    """Start the FastAPI server."""
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)


@app.command()
def init_db():
    """Initialize the database and seed with data."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database_from_config(session, settings.default_seed_path)
    typer.echo("Database initialized and seeded.")


@app.command()
def export():
    """Export state to JSON."""
    with SessionLocal() as session:
        state = export_state(session)
        print(state)


@app.command()
def import_cmd(file: str):
    """Import state from JSON file."""
    with open(file) as f:
        json_str = f.read()
    with SessionLocal() as session:
        import_state(session, json_str)
    typer.echo("State imported.")


if __name__ == "__main__":
    app()