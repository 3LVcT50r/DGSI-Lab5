# Provider App PRD

## Overview

The Provider App is a companion CLI + REST service that simulates the upstream materials supplier used by the 3D Printer Factory Simulation. It exposes a vendor catalog, stock levels, pricing tiers, order lifecycle, day advancement, and state import/export.

## Goals

- Provide a realistic supplier simulation for integration testing and backend orchestration.
- Support both interactive CLI commands and REST API access.
- Persist simulation state across restarts using SQLite.
- Enable reproducible seeding from a JSON provider catalog.

## Core Features

- Products catalog with product descriptions, lead times, pricing tiers, and part categories such as PCBs, extruders, kits, cables, transformers.
- Stock tracking for each product.
- Purchase order lifecycle with statuses and event logging.
- Simulation day clock persisted in state.
- Export/import of full app state as JSON.
- REST API to access catalog, inventory, orders, and day control.

## Data Model

### Products
- `id`: integer primary key
- `name`: product code / SKU
- `description`: text
- `lead_time_days`: days from order placement to delivery

### Pricing Tiers
- `id`: integer primary key
- `product_id`: foreign key to product
- `min_quantity`: minimum units for this tier
- `unit_price`: price per unit for quantities at or above this tier
- Example: 1–9 units at 50 EUR each, 10–99 units at 35 EUR each, 100+ units at 25 EUR each.

### Stock
- `product_id`: primary key referencing product
- `quantity`: current units in inventory

### Orders
- `id`: integer primary key
- `buyer`: buyer name / identifier
- `product_id`: product ordered
- `quantity`: ordered units
- `unit_price`: applied unit price for order quantity
- `total_price`: computed order total
- `placed_day`: day order was placed
- `expected_delivery_day`: delivery day computed using lead time
- `shipped_day`: day order transitioned to shipped
- `delivered_day`: day order delivered
- `status`: one of `pending`, `shipped`, `delivered`

### Events
- `id`: integer primary key
- `sim_day`: simulation day when event occurred
- `event_type`: event category (e.g. `order_placed`, `order_shipped`, `order_delivered`, `day_advanced`)
- `entity_type`: affected entity type
- `entity_id`: affected entity id
- `detail`: free-form JSON text
- `created_at`: timestamp

### Simulation State
- `key`: primary key string
- `value`: persisted state value

Supported state keys:
- `current_day`

## CLI Commands

### Catalog
- `provider-cli catalog` — list products and pricing tiers

### Stock
- `provider-cli stock` — show current inventory

### Orders
- `provider-cli orders list [--status STATUS]` — list orders, optional status filter
- `provider-cli orders show <order_id>` — show order details

### Pricing
- `provider-cli price set <product> <tier> <price>` — update a pricing tier by product and minimum quantity

### Stock Management
- `provider-cli restock <product> <quantity>` — add inventory to provider stock

### Day Control
- `provider-cli day advance` — process one simulation day
- `provider-cli day current` — show current simulation day

### Import / Export
- `provider-cli export` — dump full state as JSON
- `provider-cli import <file>` — load state from JSON

### REST API
- `provider-cli serve --port 8001` — expose the REST API on the selected port

## REST API Endpoints

### GET /api/catalog
Return products and pricing tiers.

### GET /api/stock
Return current inventory levels.

### POST /api/orders
Place a purchase order.

### GET /api/orders
List orders, optional query `?status=pending|shipped|delivered`.

### GET /api/orders/{id}
Return order details.

### POST /api/day/advance
Advance one simulation day.

### GET /api/day/current
Return the current simulation day.

## Order Workflow

### Placing an Order
- Request: buyer, product, quantity.
- Provider checks stock availability and computes applicable unit price using pricing tiers.
- Computes expected delivery day: `current_day + lead_time_days`.
- Creates order in `pending` status.
- Writes an `order_placed` event.

### Advancing a Day
1. Deliver orders where `status == shipped` and `expected_delivery_day == current_day`:
   - set `status` -> `delivered`
   - set `delivered_day` to current day
   - emit `order_delivered`
2. Advance `pending` orders with available stock:
   - decrement stock
   - set `status` -> `shipped`
   - set `shipped_day` to current day
   - emit `order_shipped`
3. Increment `current_day`.
4. Emit `day_advanced` event.

## The Order Lifecycle
- All orders use the same explicit state machine.
- Order state must be represented as explicit status values in code and the database, not by implicit boolean flags.
- Code should use enum-style states and clearly defined transitions, with events recording each state change.
- States in the lifecycle include:
  - `pending`
  - `confirmed`
  - `in_progress`
  - `shipped`
  - `delivered`
  - `rejected`
  - `cancelled`
- Valid transitions are:
  - `pending` → `confirmed`
  - `pending` → `rejected`
  - `pending` → `cancelled`
  - `confirmed` → `in_progress`
  - `in_progress` → `shipped`
  - `shipped` → `delivered`

## The Ironclad Rule
- Parts ordered today cannot arrive today.
- Minimum lead time is 1 day.
- If a provider has a 3-day lead time, an order placed on day N arrives on day N+3.
- This rule is essential for simulation tension: agents must plan ahead and cannot react to a shortage on the same day it occurs.

## Suggested Database Schema

CREATE TABLE products (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  lead_time_days INTEGER NOT NULL
);

CREATE TABLE pricing_tiers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL,
  min_quantity INTEGER NOT NULL,
  unit_price REAL NOT NULL,
  FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE stock (
  product_id INTEGER PRIMARY KEY,
  quantity INTEGER NOT NULL,
  FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  buyer TEXT NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  unit_price REAL NOT NULL,
  total_price REAL NOT NULL,
  placed_day INTEGER NOT NULL,
  expected_delivery_day INTEGER NOT NULL,
  shipped_day INTEGER,
  delivered_day INTEGER,
  status TEXT NOT NULL,
  FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sim_day INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  entity_type TEXT,
  entity_id INTEGER,
  detail TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sim_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

`sim_state` holds the current day so it survives restarts.

## Seed Data

The application initializes from `seed-provider.json`, which defines a starting product catalog, pricing tiers, and stock levels.

Example seed structure:
```json
{
  "products": [
    {
      "name": "pcb",
      "description": "Main control board",
      "lead_time_days": 3,
      "pricing": [
        {"min_qty": 1, "price": 40},
        {"min_qty": 20, "price": 32},
        {"min_qty": 200, "price": 25}
      ],
      "initial_stock": 500
    },
    {
      "name": "extruder",
      "description": "Hot-end extruder",
      "lead_time_days": 5,
      "pricing": [
        {"min_qty": 1, "price": 60},
        {"min_qty": 10, "price": 50}
      ],
      "initial_stock": 200
    }
  ]
}
```

## Success Criteria

- CLI supports all requested commands.
- REST API mirrors CLI behavior.
- State is persisted in SQLite and survives restart.
- Seed file can populate a fresh database reproducibly.
- Export/import round-trips state successfully.
