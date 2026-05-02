"""Command-line interface for the factory app."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import httpx
from src.config import Settings


def load_providers(settings: Settings) -> List[Dict[str, Any]]:
    """Load configured manufacturer providers from default config."""
    config_path = settings.default_config_path
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    manufacturer = config.get(
        "manufacturer",
        {"port": 8002, "providers": []}
    )
    return manufacturer.get("providers", [])


def find_provider(providers: List[Dict[str, Any]], name: str) -> Dict[str, Any]:
    """Find a provider by name (case-insensitive)."""
    normalized = name.strip().lower()
    for provider in providers:
        if provider.get("name", "").strip().lower() == normalized:
            return provider
    raise ValueError(f"Supplier '{name}' is not configured.")


def print_provider_catalog(provider: Dict[str, Any]) -> None:
    """Fetch and print provider catalog from provider API."""
    url = provider["url"] + "/api/v1/catalog"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        catalog = response.json()

    if not catalog:
        print("No catalog items found.")
        return
    print(f"Catalog for {provider['name']} ({provider['url']}):")
    for item in catalog:
        print(f"Product: {item['product']['name']} ({item['product']['description']})")
        print(f"  Lead time: {item['product']['lead_time_days']} days")
        for tier in item['pricing_tiers']:
            print(f"  Qty {tier['min_quantity']}+: ${tier['price']:.2f}")
        print()


def create_purchase_order(provider: Dict[str, Any], product_id: int, quantity: float) -> Dict[str, Any]:
    """Place a purchase order with the specified provider."""
    url = provider["url"].rstrip("/") + "/api/v1/orders"
    payload = {"product_id": product_id, "quantity": quantity}
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def list_provider_orders(provider: Dict[str, Any]) -> List[Dict[str, Any]]:
    """List all orders from a provider."""
    url = provider["url"].rstrip("/") + "/api/v1/orders"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def serve_app(port: int) -> None:
    """Start the factory FastAPI server."""
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manufacturer CLI for factory-app"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    suppliers_parser = subparsers.add_parser("suppliers", help="Supplier/provider commands")
    suppliers_sub = suppliers_parser.add_subparsers(dest="subcommand", required=True)
    suppliers_sub.add_parser("list", help="List configured providers")
    catalog_parser = suppliers_sub.add_parser("catalog", help="Show provider catalog")
    catalog_parser.add_argument("supplier_name", type=str, help="Configured provider name")

    purchase_parser = subparsers.add_parser("purchase", help="Purchase order commands")
    purchase_sub = purchase_parser.add_subparsers(dest="subcommand", required=True)
    purchase_sub.add_parser("list", help="List purchase orders placed with providers")
    purchase_create = purchase_sub.add_parser("create", help="Create a purchase order")
    purchase_create.add_argument("--supplier", required=True, type=str, help="Provider name")
    purchase_create.add_argument("--product", required=True, type=int, help="Product ID")
    purchase_create.add_argument("--qty", required=True, type=float, help="Quantity")

    serve_parser = subparsers.add_parser("serve", help="Start the REST API server")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to serve on")

    args = parser.parse_args()
    settings = Settings()
    providers = load_providers(settings)

    if args.command == "suppliers":
        if args.subcommand == "list":
            if not providers:
                print("No configured providers.")
                return
            print("Configured providers:")
            for provider in providers:
                print(f"- {provider.get('name')} ({provider.get('url')})")
        elif args.subcommand == "catalog":
            try:
                provider = find_provider(providers, args.supplier_name)
                print_provider_catalog(provider)
            except ValueError as exc:
                print(exc)
    elif args.command == "purchase":
        if args.subcommand == "list":
            if not providers:
                print("No configured providers.")
                return
            for provider in providers:
                print(f"Orders from {provider.get('name')} ({provider.get('url')}):")
                orders = list_provider_orders(provider)
                if not orders:
                    print("  No orders found.")
                else:
                    for order in orders:
                        order_id = order.get("id")
                        product_id = order.get("product_id")
                        quantity = order.get("quantity")
                        status = order.get("status")
                        expected = order.get("expected_delivery_day")
                        print(f"  - Order {order_id}: product={product_id}, qty={quantity}, status={status}, expected_delivery={expected}")
                print()
        elif args.subcommand == "create":
            try:
                provider = find_provider(providers, args.supplier)
                created = create_purchase_order(provider, args.product, args.qty)
                print("Purchase order created:")
                print(json.dumps(created, indent=2))
            except ValueError as exc:
                print(exc)
            except httpx.HTTPError as exc:
                print(f"Failed to create purchase order: {exc}")
    elif args.command == "serve":
        serve_app(args.port)


if __name__ == "__main__":
    main()
