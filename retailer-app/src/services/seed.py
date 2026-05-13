"""Seed the database with initial configuration data."""

import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from src.models import (
    Product,
    Stock,
    SimState,
)

logger = logging.getLogger(__name__)


def seed_database_from_config(
    session: Session, config_path: str
):
    """Seed the DB with products and initial state."""
    if session.query(SimState).first():
        logger.info(
            "Database already seeded. Skipping."
        )
        return

    logger.info(
        "Seeding database from config: %s", config_path
    )
    with open(config_path, "r") as f:
        config_data = json.load(f)

    # 1. Initialize SimState
    state = SimState(current_day=0)
    session.add(state)

    # 2. Create products from manufacturer catalog
    manufacturer_url = config_data.get("manufacturer", {}).get("url", "http://localhost:8002")
    import httpx
    try:
        response = httpx.get(f"{manufacturer_url}/api/v1/products")
        response.raise_for_status()
        products_data = response.json()
        
        for prod_data in products_data:
            if prod_data["type"] == "finished":  # Only finished goods
                product = Product(
                    name=prod_data["name"],
                    wholesale_price=100.0,  # Default, will be updated
                    retail_price=150.0,     # Default markup
                )
                session.add(product)
                session.flush()
                
                # Create stock record
                stock = Stock(product_id=product.id, quantity=0)
                session.add(stock)
                
    except Exception as exc:
        logger.warning(f"Failed to fetch products from manufacturer: {exc}")
        # Fallback: create some default products
        default_products = [
            {"name": "P3D-Classic", "wholesale_price": 90.0, "retail_price": 135.0},
            {"name": "P3D-Pro", "wholesale_price": 120.0, "retail_price": 180.0},
        ]
        for prod_data in default_products:
            product = Product(**prod_data)
            session.add(product)
            session.flush()
            
            stock = Stock(product_id=product.id, quantity=0)
            session.add(stock)

    session.commit()
    logger.info("Database successfully seeded.")