import json
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Dict, Any
from src.models import Product, ProductType, BOM, Supplier, Inventory
from src.config import Settings


def load_initial_data(session: Session) -> None:
    """Load initial products, BOM, suppliers and inventory from config file."""
    settings = Settings()

    # Check if data already exists
    if session.query(Product).count() > 0:
        return  # Data already loaded

    config_path = settings.default_config_path
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Create products from BOM
    products_created = {}

    for model_name, model_data in config["models"].items():
        # Create finished product
        finished_product = Product(
            name=model_name,
            type=ProductType.FINISHED
        )
        session.add(finished_product)
        session.flush()  # Get ID
        products_created[model_name] = finished_product

        # Create raw materials from BOM
        for material_name, quantity in model_data["bom"].items():
            if material_name not in products_created:
                raw_product = Product(
                    name=material_name,
                    type=ProductType.RAW
                )
                session.add(raw_product)
                session.flush()
                products_created[material_name] = raw_product

            # Create BOM entry
            bom_entry = BOM(
                finished_product_id=finished_product.id,
                material_id=products_created[material_name].id,
                quantity=quantity
            )
            session.add(bom_entry)

    # Create suppliers (simplified - one supplier per raw material)
    for material_name, product in products_created.items():
        if product.type == ProductType.RAW:
            supplier = Supplier(
                name=f"Supplier_{material_name}",
                product_id=product.id,
                unit_cost=10.0,  # Default cost
                lead_time_days=3  # Default lead time
            )
            session.add(supplier)

    # Initialize inventory (empty)
    for product in products_created.values():
        inventory = Inventory(
            product_id=product.id,
            quantity=0
        )
        session.add(inventory)

    session.commit()


def clear_all_data(session: Session) -> None:
    """Clear all simulation data."""
    from src.models import Event, PurchaseOrder, ManufacturingOrder

    # Clear in order to avoid foreign key constraints
    session.query(Event).delete()
    session.query(PurchaseOrder).delete()
    session.query(ManufacturingOrder).delete()
    session.query(Inventory).delete()
    session.query(Supplier).delete()
    session.query(BOM).delete()
    session.query(Product).delete()

    session.commit()