import typer
import json
import uvicorn
from typing import Optional
from provider.database import SessionLocal, Base, engine
from provider.models import Product, PricingTier, Stock, Order, SimState, Event
from provider.main import advance_day as api_advance_day, get_current_day

app = typer.Typer(help="Provider CLI")

@app.command("catalog")
def list_catalog():
    """List products with pricing tiers."""
    with SessionLocal() as db:
        products = db.query(Product).all()
        for p in products:
            typer.echo(f"Product: {p.name} (Lead Time: {p.lead_time_days} days)")
            for tier in sorted(p.pricing_tiers, key=lambda t: t.min_quantity):
                typer.echo(f"  Tier >= {tier.min_quantity}: ${tier.unit_price:.2f}")

@app.command("stock")
def show_stock():
    """Show current inventory."""
    with SessionLocal() as db:
        stocks = db.query(Stock).all()
        for s in stocks:
            typer.echo(f"{s.product.name}: {s.quantity} units")

orders_app = typer.Typer(help="Manage orders")
app.add_typer(orders_app, name="orders")

@orders_app.command("list")
def list_orders(status: Optional[str] = None):
    """List all orders."""
    with SessionLocal() as db:
        query = db.query(Order)
        if status:
            query = query.filter(Order.status == status)
        orders = query.all()
        for o in orders:
            typer.echo(f"[{o.id}] {o.buyer} ordered {o.quantity}x {o.product.name} - Status: {o.status.value}")

@orders_app.command("show")
def show_order(order_id: int):
    """Details of one order."""
    with SessionLocal() as db:
        o = db.query(Order).filter(Order.id == order_id).first()
        if not o:
            typer.echo("Order not found.")
            return
        typer.echo(f"Order ID: {o.id}")
        typer.echo(f"Buyer: {o.buyer}")
        typer.echo(f"Product: {o.product.name}")
        typer.echo(f"Quantity: {o.quantity}")
        typer.echo(f"Unit Price: ${o.unit_price:.2f}")
        typer.echo(f"Total Price: ${o.total_price:.2f}")
        typer.echo(f"Placed Day: {o.placed_day}")
        typer.echo(f"Expected Delivery Day: {o.expected_delivery_day}")
        typer.echo(f"Shipped Day: {o.shipped_day}")
        typer.echo(f"Delivered Day: {o.delivered_day}")
        typer.echo(f"Status: {o.status.value}")

price_app = typer.Typer(help="Manage prices")
app.add_typer(price_app, name="price")

@price_app.command("set")
def set_price(product_name: str, tier: int, price: float):
    """Change a price tier."""
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.name == product_name).first()
        if not product:
            typer.echo("Product not found.")
            return
        pricing_tier = db.query(PricingTier).filter(
            PricingTier.product_id == product.id, 
            PricingTier.min_quantity == tier
        ).first()
        if pricing_tier:
            pricing_tier.unit_price = price
            typer.echo(f"Updated tier >= {tier} for {product_name} to ${price:.2f}")
        else:
            new_tier = PricingTier(product_id=product.id, min_quantity=tier, unit_price=price)
            db.add(new_tier)
            typer.echo(f"Created new tier >= {tier} for {product_name} at ${price:.2f}")
        db.commit()

@app.command("restock")
def restock(product_name: str, quantity: int):
    """Add to own stock (simulated upstream)."""
    with SessionLocal() as db:
        product = db.query(Product).filter(Product.name == product_name).first()
        if not product:
            typer.echo("Product not found.")
            return
        stock = db.query(Stock).filter(Stock.product_id == product.id).first()
        if stock:
            stock.quantity += quantity
        else:
            stock = Stock(product_id=product.id, quantity=quantity)
            db.add(stock)
        db.commit()
        typer.echo(f"Restocked {quantity} units of {product_name}. New stock: {stock.quantity}")

day_app = typer.Typer(help="Manage simulated time")
app.add_typer(day_app, name="day")

@day_app.command("advance")
def advance_day():
    """Process one day."""
    with SessionLocal() as db:
        result = api_advance_day(db)
        typer.echo(f"Advanced to day {result['current_day']}")

@day_app.command("current")
def current_day():
    """Show current simulation day."""
    with SessionLocal() as db:
        day = get_current_day(db)
        typer.echo(f"Current Day: {day}")

@app.command("export")
def export_state(file: str):
    """Dump state to JSON."""
    with SessionLocal() as db:
        data = {"products": []}
        products = db.query(Product).all()
        for p in products:
            p_data = {
                "name": p.name,
                "description": p.description,
                "lead_time_days": p.lead_time_days,
                "pricing": [],
                "initial_stock": 0
            }
            for t in p.pricing_tiers:
                p_data["pricing"].append({"min_qty": t.min_quantity, "price": t.unit_price})
            
            stock = db.query(Stock).filter(Stock.product_id == p.id).first()
            if stock:
                p_data["initial_stock"] = stock.quantity
                
            data["products"].append(p_data)
            
        with open(file, "w") as f:
            json.dump(data, f, indent=2)
        typer.echo(f"Exported state to {file}")

@app.command("import")
def import_state(file: str):
    """Load state from JSON (used for seed loading)."""
    with open(file, "r") as f:
        data = json.load(f)
    
    with SessionLocal() as db:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        for p_data in data.get("products", []):
            prod = Product(
                name=p_data["name"],
                description=p_data.get("description", ""),
                lead_time_days=p_data["lead_time_days"]
            )
            db.add(prod)
            db.flush() # get ID
            
            for t_data in p_data.get("pricing", []):
                tier = PricingTier(
                    product_id=prod.id,
                    min_quantity=t_data["min_qty"],
                    unit_price=t_data["price"]
                )
                db.add(tier)
            
            stock = Stock(
                product_id=prod.id,
                quantity=p_data.get("initial_stock", 0)
            )
            db.add(stock)
            
        db.commit()
        typer.echo(f"Successfully imported state from {file}")

@app.command("serve")
def serve(port: int = 8001):
    """Start the REST API."""
    typer.echo(f"Starting Provider REST API on port {port}...")
    uvicorn.run("provider.main:app", host="0.0.0.0", port=port, reload=True)

if __name__ == "__main__":
    app()
