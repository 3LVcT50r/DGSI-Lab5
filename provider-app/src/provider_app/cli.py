import json
from pathlib import Path
from typing import Optional

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from provider_app.config import settings
from provider_app.database import SessionLocal, init_db
from provider_app.services import (
    advance_day,
    export_state,
    get_catalog,
    get_current_day,
    get_order,
    get_orders,
    get_stock,
    import_state,
    load_seed,
    place_order,
    restock,
    set_price_tier,
)

console = Console()
app = typer.Typer()
orders_app = typer.Typer()
price_app = typer.Typer()
day_app = typer.Typer()
app.add_typer(orders_app, name="orders")
app.add_typer(price_app, name="price")
app.add_typer(day_app, name="day")

DEFAULT_EXPORT_FILE = Path("provider-export.json")


def ensure_database() -> None:
    init_db()
    with SessionLocal() as session:
        load_seed(session, settings.seed_path)


def _display_table(columns, rows):
    table = Table(show_header=True, header_style="bold cyan")
    for column in columns:
        table.add_column(column)
    for row in rows:
        table.add_row(*[str(value) for value in row])
    console.print(table)


@app.command()
def catalog() -> None:
    "List all products and pricing tiers."
    ensure_database()
    with SessionLocal() as session:
        catalog_data = get_catalog(session)
    table = Table(show_header=True, header_style="bold green")
    table.add_column("ID")
    table.add_column("Product")
    table.add_column("Lead Time")
    table.add_column("Pricing")
    for product in catalog_data:
        pricing = ", ".join(
            f"{tier['min_quantity']}+ @ {tier['unit_price']}" for tier in product["pricing"]
        )
        table.add_row(
            str(product["id"]),
            product["name"],
            str(product["lead_time_days"]),
            pricing,
        )
    console.print(table)


@app.command()
def stock() -> None:
    "Show current inventory."
    ensure_database()
    with SessionLocal() as session:
        stock_data = get_stock(session)
    _display_table(["Product ID", "Product", "Quantity"], [
        (item["product_id"], item["product_name"], item["quantity"]) for item in stock_data
    ])


@orders_app.command("list")
def list_orders(status: Optional[str] = typer.Option(None, help="Filter by order status")) -> None:
    "List orders, optionally filtered by status."
    ensure_database()
    with SessionLocal() as session:
        orders = get_orders(session, status)
    _display_table(
        ["ID", "Buyer", "Product", "Qty", "Status", "Expected"] ,
        [
            (
                order["id"],
                order["buyer"],
                order["product"],
                order["quantity"],
                order["status"],
                order["expected_delivery_day"],
            )
            for order in orders
        ],
    )


@orders_app.command("show")
def show_order_cmd(order_id: int) -> None:
    "Show details for one order."
    ensure_database()
    with SessionLocal() as session:
        order = get_order(session, order_id)
    if not order:
        console.print(f"[red]Order {order_id} not found.[/red]")
        raise typer.Exit(code=1)
    console.print_json(data=order)


@price_app.command("set")
def set_price(product: str, tier: int, price: float) -> None:
    "Change a price tier for a product."
    ensure_database()
    with SessionLocal() as session:
        try:
            set_price_tier(session, product, tier, price)
            console.print(f"Updated price tier {tier} for {product} to {price}.")
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1)


@app.command()
def restock_cmd(product: str, quantity: int) -> None:
    "Add stock to the provider inventory."
    ensure_database()
    with SessionLocal() as session:
        try:
            restock(session, product, quantity)
            console.print(f"Restocked {quantity} units of {product}.")
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1)


@day_app.command("advance")
def advance() -> None:
    "Process one simulation day."
    ensure_database()
    with SessionLocal() as session:
        summary = advance_day(session)
    console.print_json(data=summary)


@day_app.command("current")
def current() -> None:
    "Show current simulation day."
    ensure_database()
    with SessionLocal() as session:
        day = get_current_day(session)
    console.print(f"Current day: [bold]{day}[/bold]")


@app.command("export")
def export_state_cmd(file: Optional[Path] = DEFAULT_EXPORT_FILE) -> None:
    "Export state to JSON."
    ensure_database()
    with SessionLocal() as session:
        data = export_state(session)
    with open(file, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    console.print(f"Exported state to [green]{file}[/green].")


@app.command("import")
def import_state_cmd(file: Path) -> None:
    "Import state from JSON."
    ensure_database()
    with open(file, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    with SessionLocal() as session:
        import_state(session, payload)
    console.print(f"Imported state from [green]{file}[/green].")


@app.command("serve")
def serve(port: int = typer.Option(8001, help="Port to run the REST API on.")) -> None:
    "Start the REST API server."
    ensure_database()
    uvicorn.run("provider_app.api:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    app()
