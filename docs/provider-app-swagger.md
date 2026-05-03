# Provider App Swagger Documentation

Base URL: `http://localhost:8001/api/v1`

## Interactive Swagger UI

- `http://localhost:8001/docs`
- `http://localhost:8001/redoc`

## Catalog

- `GET /catalog`
  - Get the provider product catalog with pricing.

## Stock

- `GET /stock`
  - Get current provider stock levels.

## Orders

- `GET /orders`
  - List all provider orders.
  - Optional query parameter: `status` to filter by order status.

- `GET /orders/{order_id}`
  - Get details for a specific provider order.

- `POST /orders`
  - Place a new provider order.
  - Request body includes order details from `OrderCreate` schema.

## Day Simulation

- `POST /day/advance`
  - Advance the provider simulation by one day.

- `GET /day/current`
  - Get the current simulated day.

- `POST /day/reset`
  - Reset the provider simulation to initial configuration.

## Events

- `GET /events`
  - Get provider event history.

## Notes

- Paths are mounted under `/api/v1`.
- The interactive Swagger UI reads the same OpenAPI schema used by FastAPI.
