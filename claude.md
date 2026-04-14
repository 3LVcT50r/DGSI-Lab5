# Project: 3D Printer Production Simulator

## What This Is

A discrete-event simulation system that models the day-by-day production lifecycle of a 3D printer manufacturing factory. The system puts the user in the role of production planner, requiring them to balance inventory levels, production capacity, supplier lead times, and stochastic customer demand. Each simulated day generates random manufacturing orders, processes purchase arrivals, completes production, and consumes materials — all logged for historical tracking and analysis.

## Tech Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Language | Python 3.11+ | Readability, ecosystem |
| Simulation | SimPy | Discrete-event engine with event queue, preemption, process modeling |
| Backend/API | FastAPI + Pydantic | Auto-generated OpenAPI docs, async support, type validation |
| UI | Streamlit | Rapid prototyping, matplotlib integration, no client setup |
| Charts | matplotlib | Direct Streamlit compatibility |
| Persistence | SQLite | Lightweight, portable, queryable |
| Import/Export | JSON | State persistence, round-trip integrity |
| Version Control | Git + GitHub | Standard workflow |

**Alternative:** If SimPy proves too complex, a simplified turn-based loop may be used (justify in implementation notes).

## Architecture

### Layered Design

```
Streamlit UI → FastAPI Routes → Business Logic Services → Persistence Layer
                                    ↓
                            SimPy Simulation Engine
```

### Key Decisions

- **Separation of Concerns:** API routes contain no business logic; all operations go through service layer
- **Event Sourcing Lite:** All state changes logged as events for audit trail and charting
- **Atomic Operations:** Database transactions wrap multi-step operations (release order, consume materials)
- **Configuration First:** BOM, suppliers, demand parameters loaded from JSON before simulation starts

### Simulation Flow (per day)

1. Increment day counter
2. Generate new manufacturing orders (random, configurable)
3. Process purchase order arrivals (based on lead time)
4. Complete in-progress production orders
5. Start new orders (up to daily capacity)
6. Consume raw materials
7. Log all events

## Data Model

### Core Entities

```
Product ──┬── BOM ──► Product (materials)
          │
          ├── Inventory
          │
          ├── ManufacturingOrder
          │     └── status: pending → in_progress → completed
          │
          └── PurchaseOrder
                └── status: open → received → cancelled

Supplier ──► PurchaseOrder

Event (logs all state changes)
```

### Entities Overview

| Entity | Purpose | Key Fields |
|--------|---------|------------|
| `Product` | Raw materials and finished goods | id, name, type (raw/finished) |
| `BOM` | Materials needed per product | product_id, material_id, quantity |
| `Supplier` | Who sells what at what price | name, product_id, unit_cost, lead_time_days |
| `Inventory` | Current stock levels | product_id, quantity, reserved |
| `ManufacturingOrder` | Customer demand | product_id, quantity, status, dates |
| `PurchaseOrder` | Replenishment requests | supplier_id, product_id, quantity, expected_delivery |
| `Event` | Audit trail | type, sim_date, details (JSON) |

## API Endpoints

### Simulation Control
- `POST /api/v1/simulate/advance` — Advance one day
- `GET /api/v1/simulate/status` — Current state
- `POST /api/v1/simulate/reset` — Reset to start

### Orders
- `GET /api/v1/orders` — List all MOs
- `POST /api/v1/orders/{id}/release` — Release to production
- `DELETE /api/v1/orders/{id}` — Cancel pending

### Inventory & Purchasing
- `GET /api/v1/inventory` — Stock levels
- `GET /api/v1/suppliers` — Supplier catalog
- `POST /api/v1/purchase-orders` — Create PO

### Import/Export
- `GET /api/v1/state/export` — Full state as JSON
- `POST /api/v1/state/import` — Restore state

*Full spec at `/docs` (Swagger UI)*

## Coding Conventions

- **Type hints everywhere** — No bare `def func()` without annotations
- **Pydantic models** — All API request/response schemas validated at boundaries
- **Routes separate from logic** — `src/api/*.py` calls `src/services/*.py`
- **Docstrings** — Google-style for all public functions and classes
- **Config via env/files** — `.env` or `config.json`, never hardcoded
- **SQLAlchemy models** — Defined in `src/models/`, schemas in `src/schemas/`
- **Single responsibility** — One class/function per concern

### File Naming
- `snake_case` for files and modules
- Test files: `test_<module>.py`
- API routes: `<domain>.py` (e.g., `orders.py`, `purchasing.py`)

### Error Handling
- Custom exception hierarchy in `src/exceptions.py`
- HTTPException for API errors with appropriate status codes
- Graceful degradation — simulation continues even if optional feature fails

## Project Structure

```
DGSI-Lab5/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + CORS config
│   ├── config.py            # Settings (pydantic-settings)
│   ├── database.py          # SQLite + SQLAlchemy session
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic DTOs
│   ├── services/            # Business logic
│   └── api/                 # Route handlers
├── tests/
│   ├── fixtures/
│   └── test_*.py
├── data/
│   ├── database.sqlite
│   └── default_config.json
├── requirements.txt
├── README.md
├── prd.md
└── claude.md
```

## Development Workflow

1. Read relevant files before modifying (never edit blind)
2. Update this `claude.md` "Current State" after each major change
3. Add/modify tests when changing business logic
4. Run `fastapi dev src/main.py` to verify API
5. Run `streamlit run src/ui/app.py` to verify UI
6. Commit small, frequent changes with descriptive messages

## Current State

| Area | Status | Notes |
|------|--------|-------|
| PRD | ✅ Done | `prd.md` complete |
| Project Setup | ✅ Done | Requirements.txt, folder structure, scripts de ejecución |
| Database Schema | ✅ Done | SQLAlchemy models completos con todas las entidades |
| Configuration | ✅ Done | Default BOM, suppliers, demand params en JSON |
| Simulation Engine | ✅ **Implemented** | Lógica de simulación básica funcionando (carga inicial, estado, advance day) |
| API Layer | ✅ **Implemented** | Endpoints REST completos con datos reales |
| UI Dashboard | ✅ **Implemented** | Streamlit conectada al backend con funcionalidades completas |
| Tests | ⚠️ Basic | Tests básicos funcionando, faltan tests de integración |
| Charts & Historical Data | ✅ **Implemented** | Dashboard completo con 5 pestañas de gráficos y métricas históricas |

**Next Up:** Implementar import/export de estado JSON y agregar manejo de errores avanzado.

**Next Up:** Refinar la lógica de simulación (capacidad de producción, demanda realista) y agregar export/import de estado.

## Example Production Plan

```json
{
  "capacity_per_day": 10,
  "warehouse_capacity": 500,
  "models": {
    "P3D-Classic": {
      "assembly_time_hours": 4,
      "bom": {
        "kit_piezas": 1,
        "pcb": 1,
        "pcb_ref": "CTRL-V2",
        "extrusor": 1,
        "cables_conexion": 2,
        "transformador_24v": 1,
        "enchufe_schuko": 1
      }
    },
    "P3D-Pro": {
      "assembly_time_hours": 6,
      "bom": {
        "kit_piezas": 1,
        "pcb": 1,
        "pcb_ref": "CTRL-V3",
        "extrusor": 1,
        "sensor_autonivel": 1,
        "cables_conexion": 3,
        "transformador_24v": 1,
        "enchufe_schuko": 1
      }
    }
  }
}
```

## Event Types (for logging)

- `order_created` — New manufacturing order generated
- `order_released` — User released order to production
- `order_started` — Production began on order
- `order_completed` — Finished good produced
- `po_created` — Purchase order issued
- `po_received` — Materials arrived from supplier
- `materials_consumed` — Raw materials used in production
- `stockout` — Inventory depleted while demand exists
