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
Metric CSVs are written under <app>/data/<role>_metrics.csv.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [mock %(levelname)s] %(message)s")
logger = logging.getLogger("mock_agent")


def _metrics_path(filename: str) -> Path:
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir / filename


def _append_csv(path: Path, header: list[str], row: list[Any]) -> None:
    new_file = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="") as fh:
        writer = csv.writer(fh)
        if new_file:
            writer.writerow(header)
        writer.writerow(row)


def run_provider(context: Dict[str, Any], url: str) -> None:
    day = context.get("day", 0)
    cli_wrapper = Path("..") / "provider-cli"
    try:
        stock = httpx.get(f"{url}/api/v1/stock", timeout=10.0).json()
        for item in stock:
            qty = item.get("quantity", 0)
            if qty < 100 and cli_wrapper.exists():
                product_id = item.get("product_id")
                import subprocess
                subprocess.run(
                    ["bash", str(cli_wrapper), "restock", str(product_id), "200"],
                    check=False, timeout=30,
                )
                logger.info("restocked product %s with 200 units (via CLI)", product_id)
    except Exception as exc:
        logger.warning("provider restock skipped: %s", exc)

    try:
        stock = httpx.get(f"{url}/api/v1/stock", timeout=10.0).json()
        orders = httpx.get(f"{url}/api/v1/orders", timeout=10.0).json()
        total_stock = sum(s.get("quantity", 0) for s in stock)
        pending = sum(1 for o in orders if o.get("status") == "pending")
        _append_csv(
            _metrics_path("provider_metrics.csv"),
            ["day", "stock_qty", "pending_orders"],
            [day, total_stock, pending],
        )
    except Exception as exc:
        logger.warning("provider metrics skipped: %s", exc)


def run_manufacturer(context: Dict[str, Any], url: str) -> None:
    day = context.get("day", 0)
    try:
        sales = httpx.get(f"{url}/api/v1/sales-orders", timeout=10.0).json()
        for order in sales:
            if order.get("status") == "pending":
                httpx.post(f"{url}/api/v1/sales-orders/{order['id']}/release", timeout=10.0)
    except Exception as exc:
        logger.warning("manufacturer release skipped: %s", exc)

    try:
        inv = httpx.get(f"{url}/api/v1/inventory", timeout=10.0).json()
        sales = httpx.get(f"{url}/api/v1/sales-orders", timeout=10.0).json()
        parts = sum(
            s.get("quantity", 0)
            for s in inv
            if s.get("product_type", "raw_material") == "raw_material"
        )
        printers = sum(
            s.get("quantity", 0)
            for s in inv
            if s.get("product_type") == "finished_good"
        )
        pending = sum(1 for o in sales if o.get("status") == "pending")
        _append_csv(
            _metrics_path("manufacturer_metrics.csv"),
            ["day", "parts_stock", "printer_stock", "pending_orders"],
            [day, parts, printers, pending],
        )
    except Exception as exc:
        logger.warning("manufacturer metrics skipped: %s", exc)


def run_retailer(context: Dict[str, Any], url: str) -> None:
    day = context.get("day", 0)
    try:
        orders = httpx.get(f"{url}/api/v1/orders", timeout=10.0).json()
        for order in orders:
            if order.get("status") == "pending":
                try:
                    httpx.post(f"{url}/api/v1/orders/{order['id']}/fulfill", timeout=10.0)
                except Exception:
                    httpx.post(f"{url}/api/v1/orders/{order['id']}/backorder", timeout=10.0)
    except Exception as exc:
        logger.warning("retailer fulfill skipped: %s", exc)

    try:
        catalog = httpx.get(f"{url}/api/v1/catalog", timeout=10.0).json()
        for item in catalog:
            payload = {"product_name": item["name"], "quantity": 5}
            try:
                httpx.post(f"{url}/api/v1/purchases", json=payload, timeout=10.0)
            except Exception:
                pass
    except Exception as exc:
        logger.warning("retailer reorder skipped: %s", exc)

    try:
        stock = httpx.get(f"{url}/api/v1/stock", timeout=10.0).json()
        orders = httpx.get(f"{url}/api/v1/orders", timeout=10.0).json()
        total_stock = sum(s.get("quantity_available", s.get("quantity", 0)) for s in stock)
        fulfilled = sum(1 for o in orders if o.get("status") == "fulfilled")
        backordered = sum(1 for o in orders if o.get("status") == "backordered")
        _append_csv(
            _metrics_path("retailer_metrics.csv"),
            ["day", "printer_stock", "fulfilled_orders", "backordered"],
            [day, total_stock, fulfilled, backordered],
        )
    except Exception as exc:
        logger.warning("retailer metrics skipped: %s", exc)


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
