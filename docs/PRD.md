# PRD — 3D Printer Supply Chain Simulator

## 1. Purpose & scope

Build a multi-agent supply chain simulation for a 3D-printer market. Three
independent services own a slice of the world:

- **Provider** (`:8001`) — sells parts (PCBs, kits, extruders, etc.) to manufacturers
- **Manufacturer** (`:8002`) — assembles printers from parts, sells them wholesale to retailers
- **Retailer** (`:8003`) — sells finished printers to end customers

A turn engine advances all three day-by-day, injects market signals from
scenario files, and invokes a Claude Code skill (one per role) every day.

The deliberate architectural split is **deterministic plumbing hosts
non-deterministic strategy**: the apps and the engine are deterministic Python;
the daily decisions are LLM-driven via skill files.

## 2. Architecture

### 2.1 Process layout

```
┌──────────────┐    POST /api/v1/orders    ┌────────────────┐    POST /api/v1/orders    ┌──────────────┐
│   Retailer   │─────────────────────────► │  Manufacturer  │─────────────────────────► │   Provider   │
│    :8003     │   (customer orders)       │     :8002      │   (purchase orders)       │    :8001     │
│  retailer.db │                           │  database.db   │                           │ provider.db  │
└──────┬───────┘                           └────────┬───────┘                           └──────┬───────┘
       │                                            │                                          │
       ▼                                            ▼                                          ▼
  retailer-cli                              manufacturer-cli                              provider-cli
       ▲                                            ▲                                          ▲
       │                                            │                                          │
       └────────────────────────────────┬───────────┴──────────────────────────────────────────┘
                                        │
                                turn_engine.py
                                        │
                                scenarios/*.json · skills/*.md · logs/ · runs/
```

Every app:
- Owns its own SQLite database (`<app>/data/<app>.sqlite`).
- Exposes `/api/v1/...` REST endpoints and a `*-cli` CLI sharing the service layer.
- Logs every meaningful state change into its `events` table (audit trail).
- Advances its simulated day via a `POST /api/v1/{day,simulate}/advance`.
- Snapshots a row in its `metrics` table at the end of every `advance_day`.
- Accepts `POST /api/v1/signal` to receive today's market modifiers.

### 2.2 Data model per app

**Provider** (`provider-app/src/models/`):
- `Product` — catalog (PCBs, kits, …) with `lead_time_days`.
- `PricingTier` — quantity-break pricing per product.
- `Stock` — current inventory per product.
- `Order` — purchase orders received from manufacturers; state machine
  `pending → confirmed → in_progress → shipped → delivered`.
- `Event` — append-only audit log.
- `SimState` — singleton with `current_day`.
- `SignalState` — singleton with today's `lead_time_modifier`, `supply_modifier`,
  `demand_modifier`. Read by `place_order` to inflate `expected_delivery_day`.
- `Metric` — one row per `(sim_day, product_id)` snapshotted in `advance_day`.

**Manufacturer / factory-app** (`factory-app/src/models/`):
- `Product` (raw / finished) with optional `wholesale_price` on finished goods.
- `BOM` — bill of materials linking finished products to raw components.
- `Supplier` — legacy local supplier table (Lab 5 carry-over).
- `Inventory` — per-product `quantity` and `reserved`.
- `ManufacturingOrder` — internal production orders.
- `SalesOrder` — orders received from retailers.
- `PurchaseOrder` — orders placed with the external provider.
- `SimulationState`, `Event`, `SignalState`, `Metric` — as above.

**Retailer** (`retailer-app/src/models/`):
- `Product` with `manufacturer_price` and `retail_price`.
- `Stock` — finished printers on the shelf.
- `CustomerOrder` — orders received from end customers.
- `PurchaseOrder` — orders placed with the manufacturer.
- `Sale` — completed sales (for analysis).
- `SimState`, `Event`, `SignalState`, `Metric` — as above.

### 2.3 Turn engine — order of operations per day

```
TE = turn engine, MS = market signal, EC = end customers, RA = retailer agent,
MA = manufacturer agent, PA = provider agent

TE → MS  Resolve today's signal from scenario events
TE → all  POST /api/v1/signal with the resolved modifiers
TE → EC   Generate customer orders, POST to each retailer
TE → RA   Run retailer agent (claude --print or mock)
TE → MA   Run manufacturer agent
TE → PA   Run provider agent
TE → all  POST /api/v1/day/advance (retailer first, then manufacturer, then provider)
TE → RA   GET /api/v1/day/summary → one-line per-day log
```

**Why downstream-first agents?** A retailer that decides today only sees
yesterday's manufacturer state. By running retailer → manufacturer → provider,
the retailer's purchase orders land before the manufacturer plans, and the
manufacturer's purchase orders land before the provider ships — so reactions
happen in the same turn.

**Why signal-before-agents?** The provider's `place_order` reads
`lead_time_modifier` from `SignalState` when computing `expected_delivery_day`.
If the engine pushed the signal *after* agents acted, a chip-shortage day
would produce orders with normal lead times.

### 2.4 Overlapping events in a scenario

Multiple events can be active on the same day (`holiday-rush.json` has
`chip_shortage` and `christmas_season` overlapping on days 18–20). The engine
composes modifiers conservatively:

- `demand_modifier` and `lead_time_modifier` → take the **max** (worst case
  for the manufacturer).
- `supply_modifier` → take the **min** (also the worst case — least supply).
- `price_sensitivity` → last event wins (string hint, not numeric).

Document choice: max/min keeps a single overlapping event from masking a
worse simultaneous one, and avoids silently multiplying modifiers into
unrealistic territory (e.g. 3.0 × 2.5 = 7.5x demand on Black-Friday-meets-Christmas).

## 3. APIs

### 3.1 Provider (`:8001`)

```
GET  /api/v1/catalog
GET  /api/v1/stock
GET  /api/v1/orders               # optional ?status=pending
GET  /api/v1/orders/{id}
POST /api/v1/orders               # manufacturer places a purchase order
POST /api/v1/day/advance          # one day in the lifecycle
GET  /api/v1/day/current
POST /api/v1/day/reset            # wipe + reseed
POST /api/v1/signal               # today's modifiers (NEW, Week 8)
GET  /api/v1/metrics              # snapshot rows (NEW, Week 8)
GET  /api/v1/events
```

### 3.2 Manufacturer (`:8002`)

```
GET  /api/v1/simulate/status
POST /api/v1/simulate/advance
POST /api/v1/simulate/reset
GET  /api/v1/capacity
GET  /api/v1/inventory
PUT  /api/v1/inventory/{product_id}
GET  /api/v1/sales-orders
GET  /api/v1/sales-orders/{id}
POST /api/v1/sales-orders/{id}/release
POST /api/v1/orders               # retailer places a sales order
GET  /api/v1/purchase-orders
POST /api/v1/purchase-orders      # outbound to provider
GET  /api/v1/suppliers
GET  /api/v1/bom
GET  /api/v1/pricing
PUT  /api/v1/pricing/{product_name}
POST /api/v1/signal               # NEW, Week 8
GET  /api/v1/metrics              # NEW, Week 8
```

### 3.3 Retailer (`:8003`)

```
GET  /api/v1/catalog
GET  /api/v1/stock
GET  /api/v1/orders               # customer orders
POST /api/v1/orders               # end customer places an order
POST /api/v1/orders/{id}/fulfill
POST /api/v1/orders/{id}/backorder
GET  /api/v1/purchases
POST /api/v1/purchases            # outbound to manufacturer
POST /api/v1/day/advance
GET  /api/v1/day/current
GET  /api/v1/day/summary          # NEW, Week 8 — placed/fulfilled/backordered/stockouts
POST /api/v1/signal               # NEW, Week 8
GET  /api/v1/metrics              # NEW, Week 8
```

## 4. Skill files

Skills are markdown contracts under `skills/`. Each defines: role, available
CLI commands, a numbered decision framework, a DO-NOT list, and how to
interpret market signals.

- `skills/provider-manager.md` — restock + price tiering
- `skills/manufacturer-manager.md` — release production, buy parts, set wholesale
- `skills/retail-manager.md` — fulfill, backorder, reorder, set retail price

**Iteration rule (from Week 8 PDF):** if the agent does something dumb, fix
the **skill**, not the agent.

## 5. Scenarios

Scenario JSONs under `scenarios/`. Each has `base_demand`, `base_price`, and
a list of `events` with `start_day`, `end_day`, and one or more modifiers.

- `scenarios/calm-market.json` — 25 days, all modifiers 1.0 (control group)
- `scenarios/holiday-rush.json` — 25 days; Black Friday demand×3, chip
  shortage with `supply_modifier=0.4` and `lead_time_modifier=2.0`,
  Christmas overlap with chip shortage
- `scenarios/smoke-test.json` — 10 days, baseline, for plumbing checks

## 6. Observability

Three independent layers, each consumed by a different audience:

1. **Per-day per-role agent logs** in `logs/day-{NNN}-{role}.log` (stdout of
   `claude --print` or `mock_agent`).
2. **Events table per DB** — append-only audit log.
3. **Metrics table per DB** — one snapshot row per `(sim_day, product_id)`
   inserted at the end of every `advance_day`.
4. **One-line per-day engine summary** —
   `Day 7: 12 placed / 9 fulfilled / 2 backordered / 1 stockout`,
   aggregated across retailers via `GET /api/v1/day/summary`.

`analyze_sim.py` consumes the metrics tables to produce the four Week 8
charts. `compare_scenarios.py` consumes archived `runs/<tag>/` snapshots to
produce side-by-side calm-vs-volatile panels.

## 7. Coding conventions

- Type hints on every public function.
- Pydantic models for all request/response schemas.
- Thin routes (`src/api/*.py`); business logic in `src/services/*.py`.
- Enum-typed order statuses; transitions logged into `events`.
- No secrets in source; `.env` gitignored.
- Comments only when the *why* is non-obvious.

## 8. What changed in Week 8 vs Week 7

- Added `SignalState`, `Metric` models in all three apps.
- New endpoints `/api/v1/signal`, `/api/v1/metrics` in all three apps.
- New endpoint `/api/v1/day/summary` in retailer (engine's per-day log).
- Provider `place_order` applies `lead_time_modifier` from `SignalState`.
- Each `advance_day` now snapshots metrics server-side instead of the
  mock-agent writing CSVs.
- Turn engine broadcasts the signal *before* agents act and logs the daily
  summary *after* the advance.
- Turn engine `--run-tag` archives the three SQLite files into
  `runs/<tag>/` so multiple scenario runs can be compared without colliding.
- `analyze_sim.py` rewritten to produce the four PDF-required charts
  (inventory triple-line, prices triple-line, fulfillment bars, events strip)
  with `axvspan` overlay of scenario events.
- New `compare_scenarios.py` for side-by-side panels.

## 9. Out of scope

- Authentication / multi-tenant isolation between apps.
- Persistence across machine restarts beyond the SQLite files.
- LLM-driven end customers (listed as a Week 8 stretch goal).
- Multiple competing retailers (stretch goal).
- A live Streamlit dashboard tailing the metrics tables (stretch goal).

## 10. Running

See [README.md](../README.md) at the repo root for the reproducible setup
and the exact commands per scenario.
