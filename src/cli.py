"""Manufacturer Command Line Interface."""

import typer
import json
import httpx
import uvicorn
from src.database import SessionLocal
from src.services.simulation import advance_day, get_simulation_status, create_network_purchase_order, get_inventory_levels
from src.models.purchase_order import PurchaseOrder

app = typer.Typer(help="Manufacturer CLI")

suppliers_app = typer.Typer()
app.add_typer(suppliers_app, name="suppliers", help="Manage network suppliers")

@suppliers_app.command("list")
def list_suppliers():
    """Query configured providers' /api."""
    try:
        with open("data/network_config.json", "r") as f:
            net_cfg = json.load(f)
            providers = net_cfg.get("manufacturer", {}).get("providers", [])
    except Exception:
        typer.echo("Could not load data/network_config.json")
        return

    for prov in providers:
        name = prov["name"]
        url = prov["url"]
        try:
            resp = httpx.get(f"{url}/api/catalog", timeout=2.0)
            status = "Online" if resp.status_code == 200 else "Error"
        except httpx.RequestError:
            status = "Offline"
        typer.echo(f"Supplier: {name} | URL: {url} | Status: {status}")

@suppliers_app.command("catalog")
def show_catalog(supplier_name: str):
    """Show catalog from a specific provider."""
    try:
        with open("data/network_config.json", "r") as f:
            net_cfg = json.load(f)
            providers = net_cfg.get("manufacturer", {}).get("providers", [])
    except Exception:
        typer.echo("Could not load data/network_config.json")
        return

    url = next((p["url"] for p in providers if p["name"] == supplier_name), None)
    if not url:
        typer.echo(f"Supplier {supplier_name} not configured.")
        return

    try:
        resp = httpx.get(f"{url}/api/catalog")
        resp.raise_for_status()
        products = resp.json()
        for p in products:
            typer.echo(f"Product: {p['name']} (Lead Time: {p['lead_time_days']} days)")
            for tier in sorted(p['pricing_tiers'], key=lambda t: t['min_quantity']):
                typer.echo(f"  Tier >= {tier['min_quantity']}: ${tier['unit_price']:.2f}")
    except Exception as e:
        typer.echo(f"Failed to fetch catalog: {e}")

purchase_app = typer.Typer()
app.add_typer(purchase_app, name="purchase", help="Manage purchase orders")

@purchase_app.command("create")
def create_purchase(supplier: str, product: str, qty: int):
    """Place a remote purchase order."""
    with SessionLocal() as session:
        try:
            po = create_network_purchase_order(session, supplier, product, qty)
            typer.echo(f"Created PO #{po.id} remotely with ID {po.provider_order_id}. Expected delivery: Day {po.expected_delivery}")
        except Exception as e:
            typer.echo(f"Failed to create PO: {e}")

@purchase_app.command("list")
def list_purchases():
    """List purchase orders placed with providers."""
    with SessionLocal() as session:
        pos = session.query(PurchaseOrder).filter(PurchaseOrder.provider_name != None).all()
        for po in pos:
            typer.echo(f"[{po.id}] {po.provider_name} (Remote ID: {po.provider_order_id}) - Product: {po.product.name} Qty: {po.quantity} Status: {po.status.value}")

@app.command("serve")
def serve(port: int = 8002):
    """Start the Manufacturer REST API."""
    typer.echo(f"Starting Manufacturer REST API on port {port}...")
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)

@app.command("stock")
def show_stock():
    """Show manufacturer inventory."""
    with SessionLocal() as session:
        from src.models import Inventory
        invs = session.query(Inventory).all()
        for item in invs:
            typer.echo(f"{item.product.name}: {item.quantity} units")

day_app = typer.Typer()
app.add_typer(day_app, name="day", help="Manage simulated time")

@day_app.command("advance")
def advance_sim_day():
    """Advance the simulation by one day."""
    with SessionLocal() as session:
        try:
            result = advance_day(session)
            typer.echo(f"Simulation advanced. Current day: {result['current_day']}")
        except Exception as e:
            typer.echo(f"Error advancing day: {e}")

status_app = typer.Typer()
app.add_typer(status_app, name="status", help="View simulation status")

@status_app.command("show")
def show_status():
    """Show current simulation status."""
    with SessionLocal() as session:
        try:
            status = get_simulation_status(session)
            typer.echo(f"Current Day: {status.current_day}")
            typer.echo(f"Pending Manufacturing Orders: {len(status.pending_orders)}")
            typer.echo(f"Open Purchase Orders: {len(status.open_purchase_orders)}")
        except Exception as e:
            typer.echo(f"Error fetching status: {e}")

@app.command("export")
def export_state_cmd(file: str):
    """Dump simulation state to JSON."""
    with SessionLocal() as session:
        from src.services.simulation import export_state
        data = export_state(session)
        with open(file, "w") as f:
            json.dump(data, f, indent=2)
        typer.echo(f"Exported state to {file}")

@app.command("import")
def import_state_cmd(file: str):
    """Load simulation state from JSON."""
    with SessionLocal() as session:
        from src.services.simulation import import_state
        with open(file, "r") as f:
            data = json.load(f)
        import_state(session, data)
        typer.echo(f"Imported state from {file}")

if __name__ == "__main__":
    app()
