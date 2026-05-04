"""Command-line interface for the factory app."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Union

import httpx
import uvicorn
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


def create_purchase_order(provider: Dict[str, Any], product_identifier: Union[str, int], quantity: float) -> Dict[str, Any]:
    """Place a purchase order with the specified provider.
    
    Args:
        provider: Provider configuration dict
        product_identifier: Product ID (int) or product name (str)
        quantity: Order quantity
    """
    url = provider["url"].rstrip("/") + "/api/v1/orders"
    
    # Build payload with either product_id or product_name
    payload = {"quantity": quantity}
    try:
        # Try to parse as integer
        product_id = int(product_identifier)
        payload["product_id"] = product_id
    except (ValueError, TypeError):
        # Use as product name
        payload["product_name"] = str(product_identifier)
    
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def serve_app(port: int = 8000) -> None:
    """Serve the factory FastAPI app using Uvicorn."""
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)


def list_provider_orders(provider: Dict[str, Any]) -> List[Dict[str, Any]]:
    """List all orders from a provider."""
    url = provider["url"].rstrip("/") + "/api/v1/orders"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def export_inventory(api_url: str, output_path: str | None = None) -> None:
    """Export inventory state from the factory API."""
    url = api_url.rstrip("/") + "/state/export/inventory"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        result = response.json()

    if output_path:
        with open(output_path, "w", encoding="utf-8") as out_file:
            json.dump(result, out_file, indent=2)
        print(f"Exported inventory to {output_path}")
    else:
        print(json.dumps(result, indent=2))


def export_events(api_url: str, output_path: str | None = None) -> None:
    """Export event history from the factory API."""
    url = api_url.rstrip("/") + "/state/export/events"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        result = response.json()

    if output_path:
        with open(output_path, "w", encoding="utf-8") as out_file:
            json.dump(result, out_file, indent=2)
        print(f"Exported events to {output_path}")
    else:
        print(json.dumps(result, indent=2))


def import_inventory(api_url: str, input_path: str) -> None:
    """Import inventory state into the factory API."""
    with open(input_path, "rb") as in_file:
        files = {"file": (Path(input_path).name, in_file, "application/json")}
        url = api_url.rstrip("/") + "/state/import/inventory"
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, files=files)
            response.raise_for_status()
            print(json.dumps(response.json(), indent=2))


def import_events(api_url: str, input_path: str) -> None:
    """Import event history into the factory API."""
    with open(input_path, "rb") as in_file:
        files = {"file": (Path(input_path).name, in_file, "application/json")}
        url = api_url.rstrip("/") + "/state/import/events"
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, files=files)
            response.raise_for_status()
            print(json.dumps(response.json(), indent=2))


def set_stock(api_url: str, product_id: int, quantity: float, reserved: float = 0.0) -> None:
    """Set inventory stock for a product via the factory API."""
    url = api_url.rstrip("/") + f"/inventory/{product_id}"
    payload = {"quantity": quantity, "reserved": reserved}
    with httpx.Client(timeout=10.0) as client:
        response = client.put(url, json=payload)
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))


def initialize_stock(api_url: str, input_path: str) -> None:
    """Initialize inventory stock from a JSON file via the factory API."""
    with open(input_path, "r", encoding="utf-8") as in_file:
        payload = json.load(in_file)

    url = api_url.rstrip("/") + "/inventory/initialize"
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))


def advance_day(api_url: str) -> None:
    """Advance the simulation by one day via the factory API."""
    url = api_url.rstrip("/") + "/simulate/advance"
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url)
        response.raise_for_status()
        result = response.json()
        print(f"Day advanced: {json.dumps(result, indent=2)}")


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
    purchase_create.add_argument("--product", required=True, type=str, help="Product ID (int) or product name (string)")
    purchase_create.add_argument("--qty", required=True, type=float, help="Quantity")

    export_parser = subparsers.add_parser("export", help="Export factory JSON state")
    export_sub = export_parser.add_subparsers(dest="subcommand", required=True)
    export_inventory_parser = export_sub.add_parser("inventory", help="Export inventory state")
    export_inventory_parser.add_argument(
        "--output",
        type=str,
        help="Output path for the exported inventory JSON file"
    )
    export_inventory_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000/api/v1",
        help="Factory API base URL"
    )
    export_events_parser = export_sub.add_parser("events", help="Export event history")
    export_events_parser.add_argument(
        "--output",
        type=str,
        help="Output path for the exported events JSON file"
    )
    export_events_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000/api/v1",
        help="Factory API base URL"
    )

    import_parser = subparsers.add_parser("import", help="Import factory JSON state")
    import_sub = import_parser.add_subparsers(dest="subcommand", required=True)
    import_inventory_parser = import_sub.add_parser("inventory", help="Import inventory state")
    import_inventory_parser.add_argument(
        "--input",
        required=True,
        type=str,
        help="JSON file containing inventory data"
    )
    import_inventory_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000/api/v1",
        help="Factory API base URL"
    )
    import_events_parser = import_sub.add_parser("events", help="Import event history")
    import_events_parser.add_argument(
        "--input",
        required=True,
        type=str,
        help="JSON file containing events data"
    )
    import_events_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000/api/v1",
        help="Factory API base URL"
    )

    stock_parser = subparsers.add_parser("stock", help="Inventory stock commands")
    stock_sub = stock_parser.add_subparsers(dest="subcommand", required=True)
    stock_set_parser = stock_sub.add_parser("set", help="Set stock for a product")
    stock_set_parser.add_argument("--product", required=True, type=int, help="Product ID")
    stock_set_parser.add_argument("--qty", required=True, type=float, help="Quantity")
    stock_set_parser.add_argument("--reserved", type=float, default=0.0, help="Reserved stock quantity")
    stock_set_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000/api/v1",
        help="Factory API base URL"
    )
    stock_init_parser = stock_sub.add_parser("initialize", help="Initialize inventory from JSON file")
    stock_init_parser.add_argument("--input", required=True, type=str, help="JSON file with inventory items")
    stock_init_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000/api/v1",
        help="Factory API base URL"
    )

    serve_parser = subparsers.add_parser("serve", help="Start the REST API server")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to serve on")

    day_parser = subparsers.add_parser("day", help="Simulation day commands")
    day_sub = day_parser.add_subparsers(dest="day_command", required=True)
    day_sub.add_parser("advance", help="Advance the simulation by one day")
    day_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000/api/v1",
        help="Factory API base URL"
    )

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
    elif args.command == "export":
        if args.subcommand == "inventory":
            try:
                export_inventory(args.api_url, args.output)
            except httpx.HTTPError as exc:
                print(f"Failed to export inventory: {exc}")
        elif args.subcommand == "events":
            try:
                export_events(args.api_url, args.output)
            except httpx.HTTPError as exc:
                print(f"Failed to export events: {exc}")
    elif args.command == "import":
        if args.subcommand == "inventory":
            try:
                import_inventory(args.api_url, args.input)
            except Exception as exc:
                print(f"Failed to import inventory: {exc}")
        elif args.subcommand == "events":
            try:
                import_events(args.api_url, args.input)
            except Exception as exc:
                print(f"Failed to import events: {exc}")
    elif args.command == "stock":
        if args.subcommand == "set":
            try:
                set_stock(
                    args.api_url,
                    args.product,
                    args.qty,
                    args.reserved,
                )
            except Exception as exc:
                print(f"Failed to set inventory stock: {exc}")
        elif args.subcommand == "initialize":
            try:
                initialize_stock(args.api_url, args.input)
            except Exception as exc:
                print(f"Failed to initialize inventory stock: {exc}")
    elif args.command == "day":
        if args.day_command == "advance":
            try:
                advance_day(args.api_url)
            except httpx.HTTPError as exc:
                print(f"Failed to advance day: {exc}")
    elif args.command == "serve":
        serve_app(args.port)


if __name__ == "__main__":
    main()
