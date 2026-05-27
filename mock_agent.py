#!/usr/bin/env python3
"""Deterministic stub agent used by turn_engine.py when no LLM is available.

Invoked as:
    python mock_agent.py <role> <app_url> <context_json>

The role argument can be one of:
  - "provider" or "provider-<name>"
  - "manufacturer"
  - "retailer" or "retailer-<name>"

It uses each app's REST API to reproduce a sensible-but-dumb daily turn so
the simulation has something to chew on while the LLM agent is offline.

Metrics are no longer written here — each app snapshots them server-side in
its own `advance_day` (see `snapshot_metrics` in the services modules).
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [mock %(levelname)s] %(message)s")
logger = logging.getLogger("mock_agent")

FACTORY_URL = "http://localhost:8002"
PROVIDER_URL = "http://localhost:8001"


def run_provider(context: Dict[str, Any], url: str) -> None:
    """Restock any product below a hard floor via the REST API."""
    try:
        stock = httpx.get(f"{url}/api/v1/stock", timeout=10.0).json()
    except Exception as exc:
        logger.warning("provider stock fetch failed: %s", exc)
        return

    for item in stock:
        qty = item.get("quantity", 0)
        product_id = item.get("product_id")
        if qty < 100 and product_id is not None:
            try:
                # Provider self-restocks by adding inventory directly (not an order).
                httpx.post(
                    f"{url}/api/v1/stock/restock",
                    json={"product_id": product_id, "quantity": 200},
                    timeout=10.0,
                )
                logger.info("provider %s self-restocked product %s", url, product_id)
            except Exception as exc:
                logger.warning("provider self-restock failed for %s: %s", product_id, exc)


def run_manufacturer(context: Dict[str, Any], url: str) -> None:
    """1) Release any RECEIVED sales orders.
    2) For each raw material below threshold, place a purchase order with the provider.
    """
    # Step 1: release received sales orders so they enter production.
    try:
        sales = httpx.get(f"{url}/api/v1/sales-orders", timeout=10.0).json()
    except Exception as exc:
        logger.warning("manufacturer sales fetch failed: %s", exc)
        sales = []

    for order in sales:
        status = str(order.get("status", "")).lower()
        if status in ("received", "pending"):
            try:
                httpx.post(f"{url}/api/v1/sales-orders/{order['id']}/release", timeout=10.0)
            except Exception as exc:
                logger.warning("release sales order %s failed: %s", order.get("id"), exc)

    # Step 2: order more raw materials from the provider if low.
    try:
        inv = httpx.get(f"{url}/api/v1/inventory", timeout=10.0).json()
    except Exception as exc:
        logger.warning("manufacturer inventory fetch failed: %s", exc)
        return

    # We only restock raw materials, not finished products.
    try:
        products = httpx.get(f"{url}/api/v1/products", timeout=10.0).json()
    except Exception as exc:
        logger.warning("manufacturer products fetch failed: %s", exc)
        return

    raw_ids = {p["id"] for p in products if p.get("type") == "raw"}
    threshold = 40  # restock when below this
    reorder_qty = 80

    for item in inv:
        pid = item.get("product_id")
        if pid not in raw_ids:
            continue
        qty = item.get("quantity", 0)
        if qty < threshold:
            payload = {
                "product_id": pid,
                "quantity": reorder_qty,
                "supplier_id": 1,
            }
            try:
                resp = httpx.post(f"{url}/api/v1/purchase-orders", json=payload, timeout=10.0)
                if resp.status_code < 400:
                    logger.info(
                        "manufacturer placed PO for product %s qty %s (had %s)",
                        pid, reorder_qty, qty,
                    )
                else:
                    logger.warning(
                        "manufacturer PO product %s rejected %s: %s",
                        pid, resp.status_code, resp.text,
                    )
            except Exception as exc:
                logger.warning("manufacturer PO failed for %s: %s", pid, exc)


def run_retailer(context: Dict[str, Any], url: str) -> None:
    """Fulfill what's fulfillable, backorder the rest, and order a token batch."""
    try:
        orders = httpx.get(f"{url}/api/v1/orders", timeout=10.0).json()
    except Exception as exc:
        logger.warning("retailer orders fetch failed: %s", exc)
        return

    fulfilled = backordered = 0
    for order in orders:
        # The DB enum stores statuses upper-cased ("CREATED"); be tolerant.
        status = str(order.get("status", "")).lower()
        if status != "created":
            continue
        order_id = order["id"]
        try:
            resp = httpx.post(f"{url}/api/v1/orders/{order_id}/fulfill", timeout=10.0)
        except Exception as exc:
            logger.warning("fulfill exception for %s: %s", order_id, exc)
            resp = None

        if resp is not None and resp.status_code < 400:
            fulfilled += 1
            continue

        # Fulfill rejected (likely insufficient stock) → backorder it.
        try:
            bo = httpx.post(f"{url}/api/v1/orders/{order_id}/backorder", timeout=10.0)
            if bo.status_code < 400:
                backordered += 1
            else:
                logger.warning("backorder %s rejected %s: %s", order_id, bo.status_code, bo.text)
        except Exception as exc:
            logger.warning("backorder %s failed: %s", order_id, exc)

    logger.info("retailer: fulfilled=%s backordered=%s", fulfilled, backordered)

    # Purchase a small batch of every model so the manufacturer has work to do.
    try:
        catalog = httpx.get(f"{url}/api/v1/catalog", timeout=10.0).json()
    except Exception as exc:
        logger.warning("retailer catalog fetch failed: %s", exc)
        return

    for item in catalog:
        payload = {"product_name": item["name"], "quantity": 5}
        try:
            resp = httpx.post(f"{url}/api/v1/purchases", json=payload, timeout=10.0)
            if resp.status_code >= 400:
                # E.g. manufacturer doesn't stock this model — just skip.
                logger.warning("retailer purchase %s rejected: %s", item["name"], resp.text)
        except Exception as exc:
            logger.warning("retailer purchase failed for %s: %s", item.get("name"), exc)


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: mock_agent.py <role> <app_url> <context_json>")
        sys.exit(1)

    role = sys.argv[1]
    app_url = sys.argv[2].rstrip("/")
    context = json.loads(sys.argv[3])

    if role.startswith("provider"):
        run_provider(context, app_url)
    elif role.startswith("manufacturer"):
        run_manufacturer(context, app_url)
    elif role.startswith("retailer"):
        run_retailer(context, app_url)
    else:
        logger.warning("unknown role: %s", role)


if __name__ == "__main__":
    main()
