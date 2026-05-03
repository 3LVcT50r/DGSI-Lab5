# Factory App Swagger Documentation

Base URL: `http://localhost:8000/api/v1`

## Interactive Swagger UI

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Simulation

- `GET /simulate/status`
  - Returns current simulation status.

- `POST /simulate/advance`
  - Advance the simulation by one day.

- `POST /simulate/reset`
  - Reset simulation to initial configuration.

## Orders

- `GET /orders`
  - List all manufacturing orders.

- `GET /orders/{order_id}`
  - Get details for a manufacturing order.

- `POST /orders/{order_id}/release`
  - Release a pending manufacturing order to production.

- `DELETE /orders/{order_id}`
  - Cancel a pending manufacturing order.

## Inventory

- `GET /inventory`
  - List all inventory items.

- `GET /inventory/{product_id}`
  - Get a specific inventory item.

- `PUT /inventory/{product_id}`
  - Set inventory quantity and reserved stock.
  - Request body: `quantity` (int), `reserved` (int)

- `POST /inventory/initialize`
  - Initialize inventory state from JSON array.
  - Request body: array of inventory items.

## Purchasing

- `GET /purchase-orders`
  - List all purchase orders.

- `POST /purchase-orders`
  - Create a new purchase order.
  - Request body fields:
    - `supplier_id`: int
    - `product_id`: int (optional if `product_name` provided)
    - `product_name`: string (optional if `product_id` provided)
    - `quantity`: int

- `POST /purchase-orders/{po_id}/cancel`
  - Cancel an open purchase order.

## Provider Catalog and Suppliers

- `GET /catalog`
  - Get product catalog from the provider service.

- `GET /suppliers`
  - List supplier definitions from default configuration.

- `GET /suppliers/{supplier_id}/catalog`
  - Legacy supplier catalog endpoint (may be deprecated).

## BOM

- `GET /bom`
  - List all BOM definitions.

- `GET /bom/product/{product_id}`
  - Get BOM items for a finished product.

## Products

- `GET /products`
  - List all products.

## Events & Export

- `GET /events`
  - Get recent system event history.

- `GET /state/export`
  - Export current simulation state as JSON.

- `GET /state/export/inventory`
  - Export current inventory state as JSON.

- `GET /state/export/events`
  - Export event history as JSON.

- `POST /state/import/inventory`
  - Import inventory state from uploaded JSON file.

- `POST /state/import/events`
  - Import event history from uploaded JSON file.

## Notes

- Paths are mounted under `/api/v1`.
- The interactive Swagger UI reads the same OpenAPI schema used by FastAPI.
