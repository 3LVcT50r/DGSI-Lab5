#!/usr/bin/env python3
"""Deterministic stub agent used by turn_engine.py when no LLM is available.

Invoked as:
    python mock_agent.py <role> <app_url> <context_json>

The role argument can be one of:
  - "provider" or "provider-<name>"
  - "manufacturer"
  - "retailer" or "retailer-<name>"

It uses the app's REST API to reproduce a sensible-but-dumb daily turn so the
simulation has something to chew on while the LLM agent is offline.

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


def run_provider(context: Dict[str, Any], url: str) -> None:
    """Restock any product below a hard floor via the REST API.

    The previous version invoked the bash CLI wrapper, which broke under
    Windows venvs because the wrapper hard-codes `venv/bin/python`. Using
    the API keeps this cross-platform and side-steps that whole class of
    issue.
    """
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
                httpx.post(
                    f"{url}/api/v1/orders",
                    json={"product_id": product_id, "quantity": 200, "buyer": "self-restock"},
                    timeout=10.0,
                )
                logger.info("provider %s requested self-restock for product %s", url, product_id)
            except Exception as exc:
                logger.warning("provider self-restock failed for %s: %s", product_id, exc)


def run_manufacturer(context: Dict[str, Any], url: str) -> None:
    """Release every pending sales order. Dumb but useful for plumbing tests."""
    try:
        sales = httpx.get(f"{url}/api/v1/sales-orders", timeout=10.0).json()
    except Exception as exc:
        logger.warning("manufacturer sales fetch failed: %s", exc)
        return

    for order in sales:
        if order.get("status") in ("received", "pending"):
            try:
                httpx.post(f"{url}/api/v1/sales-orders/{order['id']}/release", timeout=10.0)
            except Exception as exc:
                logger.warning("release sales order %s failed: %s", order.get("id"), exc)


def run_retailer(context: Dict[str, Any], url: str) -> None:
    """Fulfill what is fulfillable, backorder the rest, and order a token batch."""
    try:
        orders = httpx.get(f"{url}/api/v1/orders", timeout=10.0).json()
    except Exception as exc:
        logger.warning("retailer orders fetch failed: %s", exc)
        return

    for order in orders:
        if order.get("status") != "created":
            continue
        try:
            httpx.post(f"{url}/api/v1/orders/{order['id']}/fulfill", timeout=10.0)
        except Exception:
            try:
                httpx.post(f"{url}/api/v1/orders/{order['id']}/backorder", timeout=10.0)
            except Exception as exc:
                logger.warning("retailer backorder %s failed: %s", order.get("id"), exc)

    try:
        catalog = httpx.get(f"{url}/api/v1/catalog", timeout=10.0).json()
    except Exception as exc:
        logger.warning("retailer catalog fetch failed: %s", exc)
        return

    for item in catalog:
        payload = {"product_name": item["name"], "quantity": 5}
        try:
            httpx.post(f"{url}/api/v1/purchases", json=payload, timeout=10.0)
        except Exception:
            # The manufacturer may not stock this model; keep going for the others.
            pass


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
