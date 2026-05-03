"""Seed the database with initial configuration data."""

import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from src.models import Product, PricingTier, Stock, SimState

logger = logging.getLogger(__name__)


def seed_database_from_config(session: Session, config_path: Path):
    """Seed the DB with products, pricing, stock and state."""
    logger.info("Seeding database from config: %s", config_path)
    with open(config_path, "r") as f:
        config_data = json.load(f)

    # Clear existing data
    session.query(Stock).delete()
    session.query(PricingTier).delete()
    session.query(Product).delete()
    session.query(SimState).delete()

    # 1. Initialize SimState
    state = SimState(current_day=0)
    session.add(state)

    # 2. Create products
    for product_data in config_data.get("products", []):
        product = Product(
            name=product_data["name"],
            description=product_data.get("description"),
            lead_time_days=product_data.get("lead_time_days", 1)
        )
        session.add(product)
        session.flush()  # Get product.id

        # Pricing tiers
        for tier in product_data.get("pricing_tiers", []):
            pricing = PricingTier(
                product_id=product.id,
                min_quantity=tier["min_quantity"],
                price=tier["price"]
            )
            session.add(pricing)

        # Stock
        stock = Stock(
            product_id=product.id,
            quantity=product_data.get("initial_stock", 0)
        )
        session.add(stock)

    session.commit()
    logger.info("Database seeded successfully.")