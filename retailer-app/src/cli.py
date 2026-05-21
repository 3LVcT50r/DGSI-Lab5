"""Command-line interface for the retailer app."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Union

import httpx
import uvicorn
from src.config import Settings


def serve_app(port: int = 8003) -> None:
    """Serve the retailer FastAPI app using Uvicorn."""
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)


def list_catalog(api_url: str) -> None:
    """Fetch and print retailer catalog."""
    url = api_url.rstrip("/") + "/catalog"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        catalog = response.json()

    if not catalog:
        print("No catalog items found.")
        return
    print("Retailer Catalog:")
    for item in catalog:
        product = item["product"]
        print(f"Model: {product['name']}")
        print(f"  Wholesale: ${product['wholesale_price']:.2f}")
        print(f"  Retail: ${item['retail_price']:.2f}")
        print()


def list_stock(api_url: str) -> None:
    """Fetch and print current stock levels."""
    url = api_url.rstrip("/") + "/stock"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        stocks = response.json()

    if not stocks:
        print("No stock items found.")
        return
    print("Current Stock:")
    for stock in stocks:
        print(f"Product ID {stock['product_id']}: {stock['quantity']} units")
    print()


def list_customer_orders(api_url: str, status: str | None = None) -> None:
    """List customer orders."""
    url = api_url.rstrip("/") + "/orders"
    params = {}
    if status:
        params["status"] = status
    
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        orders = response.json()

    if not orders:
        print("No orders found.")
        return
    print(f"Customer Orders ({status or 'all'}):")
    for order in orders:
        print(f"Order {order['id']}: {order['customer']} ordered {order['quantity']} {order['product_id']} (status: {order['status']})")
    print()


def show_customer_order(api_url: str, order_id: int) -> None:
    """Show details of a specific customer order."""
    url = api_url.rstrip("/") + f"/orders/{order_id}"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        order = response.json()

    print(f"Order {order['id']} Details:")
    print(f"  Customer: {order['customer']}")
    print(f"  Product ID: {order['product_id']}")
    print(f"  Quantity: {order['quantity']}")
    print(f"  Status: {order['status']}")
    print(f"  Created: Day {order['created_day']}")
    if order.get('fulfilled_day'):
        print(f"  Fulfilled: Day {order['fulfilled_day']}")
    print()


def fulfill_order(api_url: str, order_id: int) -> None:
    """Fulfill a customer order."""
    url = api_url.rstrip("/") + f"/orders/{order_id}/fulfill"
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url)
        response.raise_for_status()
        result = response.json()

    print(f"Order {order_id} fulfilled:")
    print(json.dumps(result, indent=2))


def backorder_order(api_url: str, order_id: int) -> None:
    """Mark a customer order as backordered."""
    url = api_url.rstrip("/") + f"/orders/{order_id}/backorder"
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url)
        response.raise_for_status()
        result = response.json()

    print(f"Order {order_id} backordered:")
    print(json.dumps(result, indent=2))


def list_purchase_orders(api_url: str) -> None:
    """List purchase orders placed with manufacturer."""
    url = api_url.rstrip("/") + "/purchases"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        orders = response.json()

    if not orders:
        print("No purchase orders found.")
        return
    print("Purchase Orders with Manufacturer:")
    for order in orders:
        print(f"PO {order['id']}: {order['quantity']} units of product {order['product_id']} (status: {order['status']})")
    print()


def create_purchase_order(api_url: str, model: str, quantity: int) -> None:
    """Create a purchase order with the manufacturer."""
    url = api_url.rstrip("/") + "/purchases"
    payload = {"model": model, "quantity": quantity}
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        result = response.json()

    print("Purchase order created:")
    print(json.dumps(result, indent=2))


def set_price(api_url: str, model: str, price: float) -> None:
    """Set retail price for a model."""
    url = api_url.rstrip("/") + f"/catalog/{model}/price"
    params = {"price": price}
    with httpx.Client(timeout=10.0) as client:
        response = client.put(url, params=params)
        response.raise_for_status()
        result = response.json()
    print(f"Price for {model} set to ${price:.2f}")
    print(json.dumps(result, indent=2))


def advance_day(api_url: str) -> None:
    """Advance the simulation by one day."""
    url = api_url.rstrip("/") + "/day/advance"
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url)
        response.raise_for_status()
        result = response.json()
        print(f"Day advanced: {json.dumps(result, indent=2)}")


def get_current_day(api_url: str) -> None:
    """Get the current simulation day."""
    url = api_url.rstrip("/") + "/day/current"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        result = response.json()
        print(f"Current day: {result['current_day']}")


def export_state(api_url: str, output_path: str | None = None) -> None:
    """Export retailer state to JSON."""
    url = api_url.rstrip("/") + "/export"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        result = response.json()
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as out_file:
            json.dump(result, out_file, indent=2)
        print(f"Exported state to {output_path}")
    else:
        print(json.dumps(result, indent=2))


def import_state(api_url: str, input_path: str) -> None:
    """Import retailer state from JSON."""
    url = api_url.rstrip("/") + "/import"
    with open(input_path, "rb") as in_file:
        files = {"file": (Path(input_path).name, in_file, "application/json")}
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, files=files)
            response.raise_for_status()
            print(json.dumps(response.json(), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retailer CLI for retailer-app"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog_parser = subparsers.add_parser("catalog", help="Show product catalog")
    catalog_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8003/api",
        help="Retailer API base URL"
    )

    stock_parser = subparsers.add_parser("stock", help="Show current stock")
    stock_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8003/api",
        help="Retailer API base URL"
    )

    customers_parser = subparsers.add_parser("customers", help="Customer order commands")
    customers_sub = customers_parser.add_subparsers(dest="subcommand", required=True)
    
    customers_orders_parser = customers_sub.add_parser("orders", help="List customer orders")
    customers_orders_parser.add_argument(
        "--status",
        type=str,
        help="Filter by status (pending, fulfilled, backordered)"
    )
    customers_orders_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8003/api",
        help="Retailer API base URL"
    )
    
    customers_show_parser = customers_sub.add_parser("order", help="Show customer order details")
    customers_show_parser.add_argument("order_id", type=int, help="Order ID")
    customers_show_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8003/api",
        help="Retailer API base URL"
    )
    
    customers_fulfill_parser = customers_sub.add_parser("fulfill", help="Fulfill customer order")
    customers_fulfill_parser.add_argument("order_id", type=int, help="Order ID")
    customers_fulfill_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8003/api",
        help="Retailer API base URL"
    )
    
    customers_backorder_parser = customers_sub.add_parser("backorder", help="Backorder customer order")
    customers_backorder_parser.add_argument("order_id", type=int, help="Order ID")
    customers_backorder_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8003/api",
        help="Retailer API base URL"
    )

    purchase_parser = subparsers.add_parser("purchase", help="Purchase order commands")
    purchase_sub = purchase_parser.add_subparsers(dest="subcommand", required=True)
    purchase_list_parser = purchase_sub.add_parser("list", help="List purchase orders")
    purchase_list_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8003/api",
        help="Retailer API base URL"
    )
    purchase_create_parser = purchase_sub.add_parser("create", help="Create purchase order")
    purchase_create_parser.add_argument("--model", required=True, type=str, help="Model name")
    purchase_create_parser.add_argument("--qty", required=True, type=int, help="Quantity")
    purchase_create_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8003/api",
        help="Retailer API base URL"
    )

    price_parser = subparsers.add_parser("price", help="Price commands")
    price_sub = price_parser.add_subparsers(dest="subcommand", required=True)
    price_set_parser = price_sub.add_parser("set", help="Set retail price")
    price_set_parser.add_argument("--model", required=True, type=str, help="Model name")
    price_set_parser.add_argument("--price", required=True, type=float, help="Retail price")
    price_set_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8003/api",
        help="Retailer API base URL"
    )

    day_parser = subparsers.add_parser("day", help="Simulation day commands")
    day_sub = day_parser.add_subparsers(dest="day_command", required=True)
    day_sub.add_parser("advance", help="Advance the simulation by one day")
    day_sub.add_parser("current", help="Get current simulation day")
    day_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8003/api",
        help="Retailer API base URL"
    )

    export_parser = subparsers.add_parser("export", help="Export retailer state")
    export_parser.add_argument(
        "--output",
        type=str,
        help="Output path for the exported JSON file"
    )
    export_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8003/api",
        help="Retailer API base URL"
    )

    import_parser = subparsers.add_parser("import", help="Import retailer state")
    import_parser.add_argument(
        "--input",
        required=True,
        type=str,
        help="JSON file containing state data"
    )
    import_parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8003/api",
        help="Retailer API base URL"
    )

    serve_parser = subparsers.add_parser("serve", help="Start the REST API server")
    serve_parser.add_argument("--port", type=int, default=8003, help="Port to serve on")

    args = parser.parse_args()

    if args.command == "catalog":
        try:
            list_catalog(args.api_url)
        except httpx.HTTPError as exc:
            print(f"Failed to get catalog: {exc}")
    elif args.command == "stock":
        try:
            list_stock(args.api_url)
        except httpx.HTTPError as exc:
            print(f"Failed to get stock: {exc}")
    elif args.command == "customers":
        if args.subcommand == "orders":
            try:
                list_customer_orders(args.api_url, args.status)
            except httpx.HTTPError as exc:
                print(f"Failed to get orders: {exc}")
        elif args.subcommand == "order":
            try:
                show_customer_order(args.api_url, args.order_id)
            except httpx.HTTPError as exc:
                print(f"Failed to get order: {exc}")
        elif args.subcommand == "fulfill":
            try:
                fulfill_order(args.api_url, args.order_id)
            except httpx.HTTPError as exc:
                print(f"Failed to fulfill order: {exc}")
        elif args.subcommand == "backorder":
            try:
                backorder_order(args.api_url, args.order_id)
            except httpx.HTTPError as exc:
                print(f"Failed to backorder order: {exc}")
    elif args.command == "purchase":
        if args.subcommand == "list":
            try:
                list_purchase_orders(args.api_url)
            except httpx.HTTPError as exc:
                print(f"Failed to get purchase orders: {exc}")
        elif args.subcommand == "create":
            try:
                create_purchase_order(args.api_url, args.model, args.qty)
            except httpx.HTTPError as exc:
                print(f"Failed to create purchase order: {exc}")
    elif args.command == "price":
        if args.subcommand == "set":
            try:
                set_price(args.api_url, args.model, args.price)
            except Exception as exc:
                print(f"Failed to set price: {exc}")
    elif args.command == "day":
        if args.day_command == "advance":
            try:
                advance_day(args.api_url)
            except httpx.HTTPError as exc:
                print(f"Failed to advance day: {exc}")
        elif args.day_command == "current":
            try:
                get_current_day(args.api_url)
            except httpx.HTTPError as exc:
                print(f"Failed to get current day: {exc}")
    elif args.command == "export":
        try:
            export_state(args.api_url, args.output)
        except Exception as exc:
            print(f"Failed to export state: {exc}")
    elif args.command == "import":
        try:
            import_state(args.api_url, args.input)
        except Exception as exc:
            print(f"Failed to import state: {exc}")
    elif args.command == "serve":
        serve_app(args.port)


if __name__ == "__main__":
    main()