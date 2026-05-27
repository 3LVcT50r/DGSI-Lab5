# Project: 3D Printer Supply Chain Simulator

## What This Is

A multi-agent supply chain simulation built across Weeks 5–8 of the DGSI course.
Three independent FastAPI services share a simulated world via REST: a parts
**provider**, a 3D-printer **manufacturer**, and a **retailer** that sells to
end customers. A turn engine advances all three day by day, injects market
signals from scenario files, and invokes a Claude Code skill agent for each
role each day.

Architecture goal: deterministic plumbing (Python services + REST contracts)
that hosts non-deterministic strategy (LLM agents driving the daily decisions).

## Tech Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Language | Python 3.11+ | Project requirement |
| Backend / API | FastAPI + Pydantic | Auto OpenAPI docs, type validation |
| Persistence | SQLite + SQLAlchemy | One DB per app, file-based |
| CLI | argparse | One CLI per app, consistent verbs |
| Orchestration | turn_engine.py | Daily loop across all apps |
| Agents | Claude Code skills (`skills/*.md`) | LLM-driven role behaviour |
| UI | Streamlit (manufacturer + retailer) | Human-visible dashboards |
| Charts | matplotlib | Inventory/price/demand timelines |

## Architecture

```
┌──────────────┐    POST /api/v1/orders    ┌────────────────┐    POST /api/v1/orders    ┌──────────────┐
│   Retailer   │─────────────────────────► │  Manufacturer  │─────────────────────────► │   Provider   │
│    :8003     │   (customer orders)       │     :8002      │   (purchase orders)       │    :8001     │
│  retailer.db │                           │  factory.db    │                           │ provider.db  │
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
                                        ▼
                          scenarios/*.json  +  skills/*.md  +  logs/
```

Every app:
- Owns its own SQLite database.
- Exposes a `/api/v1/...` REST API and a `*-cli` CLI wrapper that share a service layer.
- Logs every meaningful state change to an `events` table (audit trail).
- Advances its simulated day via `POST /api/v1/{day,simulate}/advance`.

### Per-day order of operations

1. **Market signal.** Turn engine resolves today's scenario events into a signal
   (`demand_modifier`, `supply_modifier`, `lead_time_modifier`, `price_sensitivity`).
2. **Customer demand.** Engine POSTs auto-generated customer orders to each retailer.
3. **Retailer agent** runs (Claude Code via `claude --print`, or mock fallback).
4. **Manufacturer agent** runs.
5. **Provider agent** runs.
6. **Day advance** is POSTed to every app in order.
7. Each app appends snapshot rows to its metrics CSV (under `<app>/data/`).
8. Engine writes `logs/day-{NNN}-{role}.log` per role.

Downstream agents decide first so upstream actors can react in the same turn.

## Project Structure

```
DGSI-Lab5/
├── factory-app/          # Manufacturer service (port 8002)
│   └── src/{api,cli.py,services,models,schemas,main.py,ui}
├── provider-app/         # Parts provider service (port 8001)
│   └── src/{api,cli.py,services,models,schemas,main.py}
├── retailer-app/         # Retail store service (port 8003)
│   └── src/{api,cli.py,services,models,schemas,main.py,ui}
├── skills/
│   ├── manufacturer-manager.md
│   ├── provider-manager.md
│   └── retail-manager.md
├── scenarios/
│   ├── calm-market.json       # Steady-state control
│   ├── holiday-rush.json      # Volatile: Black Friday + chip shortage + Xmas
│   └── smoke-test.json
├── config/
│   └── sim.json               # Engine config (urls, paths, skills)
├── logs/                      # Per-day per-role agent stdout
├── tests/
├── turn_engine.py
├── mock_agent.py              # Deterministic stub when claude CLI absent
├── manufacturer-cli, provider-cli, retailer-cli   # Shell wrappers
└── enunciados/                # Original PDFs and the project brief
```

## Key API Endpoints (per app)

All apps share the same simulation-control pattern under `/api/v1`.

### Provider (`:8001`)
- `GET /catalog`, `GET /stock`, `GET /orders` (`?status=pending`)
- `POST /orders` — manufacturer places a purchase order
- `POST /day/advance`, `GET /day/current`

### Manufacturer (`:8002`)
- `GET /inventory`, `GET /sales-orders`, `GET /production/orders`, `GET /capacity`, `GET /pricing`
- `POST /orders` — retailer places a sales order
- `POST /sales-orders/{id}/release` — release to production
- `POST /purchase-orders` — outbound purchase to provider
- `POST /simulate/advance`, `GET /simulate/status`

### Retailer (`:8003`)
- `GET /catalog`, `GET /stock`, `GET /orders`
- `POST /orders` — customer order
- `POST /orders/{id}/fulfill`, `POST /orders/{id}/backorder`
- `POST /purchases` — outbound purchase to manufacturer
- `POST /day/advance`, `GET /day/current`

Full reference: each app's `/docs` (Swagger UI).

## How to run

```bash
# 1. Start the three services in separate terminals
./provider-cli      serve --port 8001
./manufacturer-cli  serve --port 8002
./retailer-cli      serve --port 8003

# 2. From the project root, run the engine
python turn_engine.py config/sim.json scenarios/holiday-rush.json 25
```

If the `claude` CLI is on `PATH`, the engine invokes `claude --print` per role
per day with the skill file in `skills/`. If not, it falls back to
`mock_agent.py`. Set `FORCE_MOCK_AGENT=1` to force the mock even with `claude`
installed (useful for cheap local testing).

## Coding conventions

- Type hints on every public function.
- Pydantic models for all request/response schemas.
- Routes are thin (`src/api/*.py`) — business logic lives in `src/services/*.py`.
- DB enums for order status (`pending|confirmed|in_progress|shipped|delivered`).
- Events written to the `events` table for every state mutation.
- No secrets in source; `.env` is gitignored.

## Skill files

Skills are the **contract** with the LLM agent. If the agent does something
dumb, fix the skill, not the agent. Each skill defines: role, available CLI
commands, a numbered decision framework, and a DO-NOT section. Skills live
under `skills/` and are referenced from `config/sim.json`.

## Logs and metrics

- `logs/day-{NNN}-{role}.log` — agent stdout for one role on one day.
- `<app>/data/{provider,manufacturer,retailer}_metrics.csv` — per-day snapshots
  for charting (used by `analyze_sim.py`).
- Every app's `events` table — full audit trail, queryable with SQL.

## Current State (Week 8 plumbing complete; runs + report pending)

| Area | Status | Notes |
|------|--------|-------|
| Three apps (provider/manufacturer/retailer) | ✅ | FastAPI + CLI + SQLite |
| REST contracts across apps | ✅ | Manufacturer ↔ Provider, Retailer ↔ Manufacturer |
| `turn_engine.py` orchestrator | ✅ | claude --print with mock fallback |
| Three skill files | ✅ | manufacturer / provider / retail managers |
| Scenarios: calm + volatile + smoke | ✅ | `calm-market.json`, `holiday-rush.json`, `smoke-test.json` |
| Per-day agent logs | ✅ | `logs/day-NNN-role.log` |
| Per-app `metrics` table (server-side snapshot) | ✅ | Written by each `advance_day` |
| `/api/v1/signal` endpoint per app | ✅ | Engine pushes today's modifiers before agents act |
| `lead_time_modifier` wired into provider | ✅ | `place_order` inflates `expected_delivery_day` |
| Engine one-line per-day summary | ✅ | `Day N: X placed / Y fulfilled / Z backordered / W stockouts` |
| `--run-tag` archives DBs to `runs/<tag>/` | ✅ | Survives the next scenario run |
| 4 required charts via `analyze_sim.py` | ✅ | Inventory · prices · fulfillment · events strip |
| Side-by-side `compare_scenarios.py` | ✅ | Calm vs volatile |
| 15+ day simulation run | ⏳ | Run on Linux box |
| Final report (PDF) and slides | ⏳ | Template in `docs/report.md` |

## Week 8 plumbing notes (what changed under the hood)

- New models in each app: `SignalState` (today's modifiers) and `Metric`
  (per-day per-product snapshot). Both created via
  `Base.metadata.create_all`; if you have pre-Week-8 SQLite files, delete
  them so the schemas recreate.
- The provider's `place_order` now applies `lead_time_modifier`. A
  `chip_shortage` event with `lead_time_modifier=2.0` therefore doubles
  the effective lead time on orders placed during the shortage.
- `mock_agent.py` no longer writes CSVs (or shells out to a bash CLI
  wrapper). All metrics now come from each app's `metrics` table.

## Known plumbing issues NOT fixed in Week 8 (deliberately deferred)

These were identified during smoke-testing and left for a Linux follow-up
because the priority was Week 8 deliverables:

1. `retailer.advance_day` calls `generate_customer_demand` internally even
   though `turn_engine.generate_customer_orders` already injects demand →
   double-generation. Workaround: comment out the internal call.
2. `factory.simulation.advance_day` calls `provider_service.advance_day()`
   itself, so the provider advances twice per turn (once by the factory,
   once by the engine).
3. `factory.simulation.advance_day` auto-generates internal manufacturing
   orders via `generate_demand` — Lab 5 residue, should be off now that
   the retailer is the source of truth.
4. `uvicorn --reload=True` is hard-coded in the apps; two processes
   sharing the same SQLite file produce `database is locked` errors under
   load. Workaround: remove `reload=True`.
5. `seed-retailer.json` lists `P3D-Mini` but `factory-app` only knows
   `P3D-Classic` and `P3D-Pro`; manufacturer 404s on Mini purchase orders.
6. Manufacturer raw-material inventory seeded to 0, so the first few days
   block on `waiting_for_materials`. Consider seeding initial parts stock.

The `runs/<tag>/` archives produced by the engine will contain reasonable
data once these are fixed; the metrics plumbing itself is correct.
