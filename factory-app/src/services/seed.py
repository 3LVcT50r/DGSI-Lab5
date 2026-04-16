import json
import logging
from typing import Dict, Any

from sqlalchemy.orm import Session
from src.models import (
    Product,
    ProductType,
    BOM,
    Supplier,
    Inventory,
    SimulationState,
)
from src.config import Settings

logger = logging.getLogger(__name__)


def seed_database_from_config(session: Session, config_path: str):
    """Seed the database with parts, BOM, suppliers and state using default config."""
    # Check if DB is already seeded:
    if session.query(SimulationState).first():
        logger.info("Database already seeded. Skipping seed process.")
        return

    logger.info(f"Seeding database from config: {config_path}")
    with open(config_path, "r") as f:
        config_data = json.load(f)

    # 1. Initialize SimulationState
    state = SimulationState(current_day=0)
    session.add(state)

    # Collect materials and models to create Products
    material_names = set()
    for model_name, model_info in config_data.get("models", {}).items():
        for mat_name in model_info.get("bom", {}).keys():
            material_names.add(mat_name)
    
    for supp in config_data.get("suppliers", []):
        for prod in supp.get("products", []):
            material_names.add(prod["product"])

    products_cache = {}

    # 2. Create raw materials
    for mat_name in material_names:
        mat_prod = Product(name=mat_name, type=ProductType.RAW)
        session.add(mat_prod)
        products_cache[mat_name] = mat_prod

    # 3. Create finished goods and their BOM
    for model_name, model_info in config_data.get("models", {}).items():
        fin_prod = Product(name=model_name, type=ProductType.FINISHED)
        session.add(fin_prod)
        products_cache[model_name] = fin_prod

    session.flush()

    for model_name, model_info in config_data.get("models", {}).items():
        fin_prod = products_cache[model_name]
        for mat_name, qty in model_info.get("bom", {}).items():
            if not isinstance(qty, (int, float)):
                logger.info(f"Skipping non-numeric BOM item: {mat_name} = {qty}")
                continue
            
            mat_prod = products_cache[mat_name]
            bom_item = BOM(
                finished_product_id=fin_prod.id,
                material_id=mat_prod.id,
                quantity=qty
            )
            session.add(bom_item)

    # 4. Create Suppliers
    for supp_info in config_data.get("suppliers", []):
        for prod_info in supp_info.get("products", []):
            product_name = prod_info["product"]
            if product_name in products_cache:
                supplier = Supplier(
                    name=supp_info["name"],
                    product_id=products_cache[product_name].id,
                    unit_cost=prod_info["price_per_unit"],
                    lead_time_days=prod_info["lead_time_days"],
                    min_order_qty=prod_info.get("min_order_qty", 1)
                )
                session.add(supplier)

    # 5. Create Inventory records at 0 for all products
    for prod in products_cache.values():
        inv = Inventory(
            product_id=prod.id,
            quantity=0,
            reserved=0
        )
        session.add(inv)

    session.commit()
    logger.info("Database successfully seeded.")
