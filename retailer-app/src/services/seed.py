"""Seed the retailer database with initial configuration data."""

import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from src.models import Product, Stock, SimState, Event

logger = logging.getLogger(__name__)


def seed_database_from_config(session: Session, config_path: str | Path):
    """Seed the DB with products, stock and initial simulated day."""
    logger.info("Seeding retailer database from config: %s", config_path)
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    session.query(Event).delete()
    session.query(Stock).delete()
    session.query(Product).delete()
    session.query(SimState).delete()

    state = SimState(current_day=0)
    session.add(state)

    for product_data in config.get("products", []):
        product = Product(
            name=product_data["name"],
            description=product_data.get("description"),
            manufacturer_price=product_data.get("manufacturer_price", 0.0),
            retail_price=product_data.get("retail_price", 0.0),
        )
        session.add(product)
        session.flush()

        stock = Stock(
            product_id=product.id,
            quantity_available=product_data.get("initial_stock", 0),
            quantity_on_hold=0.0,
        )
        session.add(stock)

    session.commit()
    logger.info("Retailer database seeded successfully.")
