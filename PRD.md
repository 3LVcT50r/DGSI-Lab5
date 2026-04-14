# Product Requirements Document (PRD)

# 3D Printer Factory Simulation System

**Version:** 1.0
**Date:** 2026-03-26
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Purpose
This document defines the requirements for a discrete-event simulation system that models the production lifecycle of a 3D printer manufacturing factory. The system puts the user in the role of production planner, requiring them to balance inventory levels, production capacity, supplier lead times, and customer demand.

### 1.2 Target Users
- Industrial engineering students learning production planning concepts
- Operations management trainers demonstrating supply chain dynamics
- Hobbyists interested in simulation and logistics

### 1.3 Success Criteria
- Successfully simulates day-by-day production cycles
- Allows users to make meaningful decisions about production and purchasing
- Provides clear visibility into inventory, orders, and events
- Exports/imports state for persistence and analysis

---

## 2. Objectives

Build a software system that simulates, day by day, the full production cycle of a factory that manufactures 3D printers. The focus is on inventory management, purchasing, and production planning.

**Key Challenges Modeled:**
- Balancing inventory costs against stockout risks
- Managing production capacity constraints
- Coordinating purchase orders with lead times
- Responding to stochastic demand patterns

---

## 3. Functional Requirements

### 3.1 R0 — Initial Configuration

**Description:** Define all static parameters required to run the simulation.

| Parameter | Type | Description |
|-----------|------|-------------|
| Bill of Materials (BOM) | Per model | Raw materials needed per finished product with quantities |
| Assembly Time | Per model | Production time required for each printer model |
| Supplier Catalog | List | Products, prices (tiered by quantity), lead times |
| Warehouse Capacity | Scalar | Maximum storage units (simplified: 1 material unit = 1 storage unit) |
| Production Capacity | Scalar | Maximum units producible per day |

**Acceptance Criteria:**
- BOM can be defined for multiple printer models
- Suppliers can offer same products at different price points
- Configuration can be persisted and loaded

### 3.2 R1 — Demand Generation

**Description:** At the start of each simulated day, manufacturing orders are generated randomly.

**Parameters:**
- Mean demand per model (configurable)
- Variance/std deviation (configurable)
- Distribution type (default: normal, truncated at 0)

**Acceptance Criteria:**
- Orders generated automatically when day advances
- Parameters configurable via UI or configuration file
- Random seed option for reproducible runs

### 3.3 R2 — Control Dashboard

**Description:** Central view displaying current state of the simulation.

**Display Elements:**
- Pending manufacturing orders with status
- BOM breakdown for each order (materials required)
- Current inventory levels (stock on hand)
- Shortage indicators (materials below threshold)

**Acceptance Criteria:**
- All data visible in single dashboard view
- Inventory updates reflect pending order reservations

### 3.4 R3 — User Decisions

**Description:** Interactive controls for production planner actions.

**User Actions:**
| Action | Inputs | Effect |
|--------|--------|--------|
| Release Order | Order ID | Moves order from pending to production queue |
| Issue Purchase Order | Supplier, Product, Quantity, Date | Creates PO; materials arrive after lead time |

**Acceptance Criteria:**
- Release only succeeds if materials available
- Purchase orders validate against supplier catalog
- User receives feedback on action success/failure

### 3.5 R4 — Event Simulation

**Description:** Core simulation logic processes events within each day cycle.

**Events Modeled:**
- Raw material consumption during manufacturing (limited by daily capacity)
- Purchase order arrivals according to supplier lead time
- Order completion notifications

**Acceptance Criteria:**
- Consumption respects capacity limits
- Lead times correctly delay material arrivals
- Events logged with timestamps

### 3.6 R5 — Calendar Advance

**Description:** Manual progression of simulated time.

**Control:** "Advance Day" button triggers 24-hour simulation cycle.

**Sequence:**
1. Increment day counter
2. Generate new demand
3. Process purchase arrivals
4. Complete in-progress production
5. Consume materials for started orders
6. Log all events

**Acceptance Criteria:**
- Single click advances simulation exactly one day
- All sub-processes execute in correct order
- UI refreshes with updated state

### 3.7 R6 — Event Log

**Description:** Historical record of all simulation events.

**Logged Events:**
- Order created
- Order released to production
- Order completed
- Material consumed
- Purchase order issued
- Purchase order received
- Stockout events

**Acceptance Criteria:**
- Every state-changing operation creates log entry
- Log supports filtering by event type/date
- Data usable for chart generation

### 3.8 R7 — JSON Import/Export

**Description:** Persist and restore simulation state.

**Exportable State:**
- Current inventory levels
- All orders (manufacturing and purchase)
- Event history
- Configuration snapshot

**Acceptance Criteria:**
- Export generates valid JSON file
- Import restores exact simulation state
- Round-trip (export then import) preserves integrity

### 3.9 R8 — REST API

**Description:** All functionality accessible via HTTP endpoints.

**Requirements:**
- Every UI capability exposed as API endpoint
- Automatic Swagger/OpenAPI documentation
- Consistent error handling and response formats
- CORS enabled for web client

**Acceptance Criteria:**
- OpenAPI spec accessible at `/docs`
- All CRUD operations testable via API
- Response schemas documented with Pydantic models

---

## 4. Non-Functional Requirements

### 4.1 Code Quality
- Clean, commented code following PEP 8
- Version controlled with Git
- Modular architecture separating concerns

### 4.2 Interface
- Simple web interface via Streamlit
- No complex client-side installation required
- Responsive layout working on standard displays

### 4.3 Portability
- Cross-platform: Windows, macOS, Linux
- Python 3.11+ runtime
- No platform-specific dependencies

### 4.4 Performance
- Simulated day processing < 1 second real time
- Dashboard renders in < 500ms
- Supports 1000+ days of simulation history

### 4.5 Data Integrity
- All state changes atomic
- No partial updates on failure
- Import validation before applying changes

---

## 5. Technical Architecture

### 5.1 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Language | Python 3.11+ | Readability, ecosystem |
| Simulation | SimPy | Discrete-event engine, battle-tested |
| Persistence | SQLite + JSON | Lightweight, portable, queryable |
| Backend/API | FastAPI + Pydantic | Auto-generated OpenAPI docs, async support |
| UI | Streamlit | Rapid prototyping, matplotlib integration |
| Charts | matplotlib | Direct Streamlit compatibility |
| Version Control | Git + GitHub | Standard workflow |

### 5.2 Alternative Simulation Approach

If SimPy is not preferred, a simplified turn-based loop may be used:

```python
def advance_day():
    day += 1
    generate_demand()
    process_purchase_arrivals()
    complete_production()
    consume_materials()
    log_events()
```

**Justification Required:** Any alternative must be justified in implementation notes explaining trade-offs vs. SimPy's event queue, preemption, and process modeling capabilities.

### 5.3 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI                           │
│  (Dashboard, Forms, Charts)                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Layer                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Orders API   │ │ Inventory API│ │ Purchasing API│       │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Simulation   │ │  Admin API   │ │  Swagger     │        │
│  │ API          │ │              │ │  /docs       │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Simulator    │ │   BOM        │ │   Inventory  │        │
│  │ Engine       │ │   Manager    │ │   Service    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Order        │ │  Purchase    │ │   Event      │        │
│  │ Manager      │ │   Manager    │ │   Logger     │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Persistence Layer                          │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │   SQLite Database   │  │   JSON Export       │          │
│  └─────────────────────┘  └─────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Data Model

### 6.1 Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Product    │       │     BOM      │       │  Manufacturer│
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │──┐    │ id (PK)      │◄─┐    │ id (PK)      │
│ name         │  │    │ product_id   │  │    │ name         │
│ type         │  └──►│ material_id  │──┘    │ contact      │
│              │      │ quantity     │       │              │
└──────────────┘      └──────────────┘       └──────────────┘
                                │                      │
                                │                      │
                     ┌──────────▼──────────┐           │
                     │    Inventory        │           │
                     ├─────────────────────┤           │
                     │ product_id (FK)     │◄──────────┘
                     │ quantity            │    ┌──────────────┐
                     │ last_updated        │    │PurchaseOrder │
                     └─────────────────────┘    ├──────────────┤
                                                │ id (PK)      │
                     ┌─────────────────────┐    │ supplier_id  │
                     │  ManufacturingOrder │    │ product_id   │
                     ├─────────────────────┤    │ quantity     │
                     │ id (PK)             │    │ issue_date   │
                     │ created_date        │    │ expected_dt  │
                     │ product_id (FK)     │    │ status       │
                     │ quantity            │    └──────────────┘
                     │ status              │
                     │ start_date          │
                     │ completed_date      │
                     └─────────────────────┘

                     ┌─────────────────────┐
                     │       Event         │
                     ├─────────────────────┤
                     │ id (PK)             │
                     │ type                │
                     │ sim_date            │
                     │ details (JSON)      │
                     └─────────────────────┘
```

### 6.2 Schema Definition

#### Product
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| name | TEXT | NOT NULL, UNIQUE |
| type | TEXT | NOT NULL CHECK(type IN ('raw', 'finished')) |

#### BOM (Bill of Materials)
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| finished_product_id | INTEGER | NOT NULL, FOREIGN KEY → Product.id |
| material_id | INTEGER | NOT NULL, FOREIGN KEY → Product.id |
| quantity | REAL | NOT NULL CHECK(quantity > 0) |

#### Supplier
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| name | TEXT | NOT NULL |
| product_id | INTEGER | NOT NULL, FOREIGN KEY → Product.id |
| unit_cost | REAL | NOT NULL |
| lead_time_days | INTEGER | NOT NULL |
| min_order_qty | INTEGER | DEFAULT 1 |

#### Inventory
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| product_id | INTEGER | NOT NULL, FOREIGN KEY → Product.id, UNIQUE |
| quantity | REAL | NOT NULL DEFAULT 0 |
| reserved | REAL | NOT NULL DEFAULT 0 |

#### ManufacturingOrder
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| created_date | INTEGER | NOT NULL |
| product_id | INTEGER | NOT NULL, FOREIGN KEY → Product.id |
| quantity | INTEGER | NOT NULL |
| status | TEXT | NOT NULL DEFAULT 'pending' |
| start_date | INTEGER | NULL |
| completed_date | INTEGER | NULL |

#### PurchaseOrder
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| supplier_id | INTEGER | NOT NULL, FOREIGN KEY → Supplier.id |
| product_id | INTEGER | NOT NULL, FOREIGN KEY → Product.id |
| quantity | INTEGER | NOT NULL |
| issue_date | INTEGER | NOT NULL |
| expected_delivery | INTEGER | NOT NULL |
| status | TEXT | NOT NULL DEFAULT 'open' |

#### Event
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| type | TEXT | NOT NULL |
| sim_date | INTEGER | NOT NULL |
| details | TEXT | NOT NULL (JSON format) |

---

## 7. Configuration Example

### 7.1 Production Plan (JSON)

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

### 7.2 Demand Configuration

```json
{
  "demand_distribution": "normal",
  "default_mean": 5,
  "default_variance": 2.0,
  "model_specific_demand": {
    "P3D-Classic": {"mean": 6, "variance": 2.5},
    "P3D-Pro": {"mean": 3, "variance": 1.5}
  },
  "random_seed": null
}
```

### 7.3 Supplier Catalog

```json
{
  "suppliers": [
    {
      "id": 1,
      "name": "Componentes ABC",
      "products": [
        {
          "product": "kit_piezas",
          "price_per_unit": 90.00,
          "lead_time_days": 3,
          "packaging": [{"qty": 1, "label": "unit"}, {"qty": 100, "label": "pallet"}]
        },
        {
          "product": "pcb",
          "price_per_unit": 25.00,
          "lead_time_days": 5,
          "packaging": [{"qty": 1, "label": "unit"}, {"qty": 50, "label": "box"}]
        }
      ]
    },
    {
      "id": 2,
      "name": "EuroComponents Ltd",
      "products": [
        {
          "product": "kit_piezas",
          "price_per_unit": 85.00,
          "lead_time_days": 7,
          "packaging": [{"qty": 1, "label": "unit"}, {"qty": 200, "label": "pallet"}]
        }
      ]
    }
  ]
}
```

---

## 8. User Interface Specification

### 8.1 Layout Overview

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER: Day [███████ 42 ███]  [ADVANCE DAY ▶]              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │ ORDERS PANEL        │  │  INVENTORY PANEL            │  │
│  ├─────────────────────┤  ├─────────────────────────────┤  │
│  │ [Pending Orders]    │  │  Material        │ Stock    │  │
│  │ • Ord #23: 8x P3D-C│  │  ───────────────────────────  │  │
│  │ • Ord #24: 6x P3D-P│  │  kit_piezas      │  22      │  │
│  │                     │  │  pcb             │  15      │  │
│  │ [Release Selected]  │  │  extrusor        │   8  🔴  │  │
│  └─────────────────────┘  │  ...                   │  │  │
│                           └─────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │ PURCHASING          │  │  PRODUCTION                 │  │
│  ├─────────────────────┤  ├─────────────────────────────┤  │
│  │ Supplier: [▼]       │  │  Daily Capacity: [████░░] 7/10│  │
│  │ Product: [▼]        │  │  Queue: 3 orders            │  │
│  │ Qty: [___]          │  │  In Progress: 4             │  │
│  │ [Issue PO]          │  │  Completed Today: 3         │  │
│  └─────────────────────┘  └─────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ CHARTS                                                  │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │ [Stock Levels Over Time]  [Completed Orders Chart]    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ EVENT LOG (Last 50)                                   │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │ Day 42: Completed order #21 (6x P3D-Pro)              │  │
│  │ Day 42: Received PO #15 (20x kit_piezas)              │  │
│  │ Day 42: Consumed materials for order #22              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Component Specifications

| Component | Type | Behavior |
|-----------|------|----------|
| Day Display | Read-only | Shows current simulation day |
| Advance Day Button | Primary Action | Triggers simulation cycle |
| Orders Table | Data Grid | Sortable, filterable, selectable |
| Inventory Panel | Status Cards | Color-coded shortage warnings |
| Supplier Dropdown | Select | Filtered by availability |
| Product Dropdown | Select | Shows purchasable items |
| Qty Input | Number | Validates against min order qty |
| Charts | Plot | matplotlib rendered in Streamlit |
| Event Log | Scrollable List | Filters by event type |

### 8.3 Color Coding

| State | Color | Usage |
|-------|-------|-------|
| Normal | Green | Inventory ≥ 2x daily need |
| Warning | Yellow | Inventory < 2x daily need |
| Critical | Red | Inventory = 0 or negative |

---

## 9. API Specification

### 9.1 Base URL
```
http://localhost:8000/api/v1
```

### 9.2 Endpoints

#### Simulation Control

| Method | Path | Description |
|--------|------|-------------|
| POST | `/simulate/advance` | Advance simulation by one day |
| GET | `/simulate/status` | Get current simulation state |
| POST | `/simulate/reset` | Reset simulation to initial state |

#### Orders

| Method | Path | Description |
|--------|------|-------------|
| GET | `/orders` | List all manufacturing orders |
| GET | `/orders/{id}` | Get specific order details |
| POST | `/orders/{id}/release` | Release order to production |
| DELETE | `/orders/{id}` | Cancel pending order |

#### Inventory

| Method | Path | Description |
|--------|------|-------------|
| GET | `/inventory` | List all inventory items |
| GET | `/inventory/{product_id}` | Get specific item stock |

#### Purchasing

| Method | Path | Description |
|--------|------|-------------|
| GET | `/purchase-orders` | List all purchase orders |
| POST | `/purchase-orders` | Create new purchase order |
| POST | `/purchase-orders/{id}/cancel` | Cancel open PO |
| GET | `/suppliers` | List all suppliers |
| GET | `/suppliers/{id}/catalog` | Get supplier product catalog |

#### BOM

| Method | Path | Description |
|--------|------|-------------|
| GET | `/bom` | List all BOM definitions |
| GET | `/bom/product/{product_id}` | Get BOM for specific product |
| GET | `/bom/calculate` | Calculate materials for order |

#### Events & History

| Method | Path | Description |
|--------|------|-------------|
| GET | `/events` | List all events (filterable) |
| GET | `/events/export` | Export events as JSON |

#### Import/Export

| Method | Path | Description |
|--------|------|-------------|
| GET | `/state/export` | Export full simulation state |
| POST | `/state/import` | Import simulation state |

### 9.3 OpenAPI Documentation

Auto-generated at `/docs` via FastAPI's built-in Swagger UI.

---

## 10. Project Structure

```
DGSI-Lab5/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # SQLite connection management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product.py
│   │   ├── bom.py
│   │   ├── order.py
│   │   ├── purchase_order.py
│   │   └── event.py
│   ├── schemas/             # Pydantic models
│   │   ├── __init__.py
│   │   ├── request.py
│   │   └── response.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── simulator.py     # SimPy simulation engine
│   │   ├── inventory.py
│   │   ├── production.py
│   │   ├── purchasing.py
│   │   └── event_logger.py
│   ├── api/                 # API route handlers
│   │   ├── __init__.py
│   │   ├── simulation.py
│   │   ├── orders.py
│   │   ├── inventory.py
│   │   ├── purchasing.py
│   │   └── export.py
│   └── ui/                  # Streamlit application
│       └── app.py
├── tests/
│   ├── __init__.py
│   ├── test_simulation.py
│   ├── test_inventory.py
│   ├── test_purchasing.py
│   └── fixtures/
│       └── sample_data.json
├── data/
│   ├── database.sqlite
│   ├── default_config.json
│   └── exports/
├── requirements.txt
├── README.md
└── prd.md
```

---

## 11. Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Project structure setup
- [ ] Database schema implementation
- [ ] Basic Pydantic models
- [ ] Configuration loading

### Phase 2: Core Simulation (Week 2)
- [ ] SimPy integration
- [ ] Demand generation
- [ ] BOM calculation
- [ ] Material consumption

### Phase 3: Business Logic (Week 3)
- [ ] Manufacturing order management
- [ ] Purchase order flow
- [ ] Inventory tracking
- [ ] Event logging

### Phase 4: API Layer (Week 4)
- [ ] REST endpoint implementation
- [ ] Request/response validation
- [ ] Error handling
- [ ] OpenAPI documentation

### Phase 5: UI Development (Week 5)
- [ ] Streamlit dashboard layout
- [ ] Component integration
- [ ] Chart visualization
- [ ] Real-time updates

### Phase 6: Polish & Testing (Week 6)
- [ ] Import/Export functionality
- [ ] Unit tests
- [ ] Integration tests
- [ ] Documentation

---

## 12. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| SimPy complexity | Medium | Low | Use simplified turn-based if needed |
| State consistency | High | Medium | Transaction wrapping, rollback on error |
| UI performance | Low | Low | Streamlit caching, pagination |
| Data migration | Low | Low | JSON schema versioning |

---

## 13. Assumptions & Dependencies

### Assumptions
- Single production line with fixed capacity
- Instantaneous order release decision
- Fixed supplier lead times (no variability)
- No production defects/scrap
- Infinite warehouse capacity (simplified constraint)

### Dependencies
- Python 3.11+ installed
- SQLite (included with Python)
- External packages via requirements.txt

---

## 14. Glossary

| Term | Definition |
|------|------------|
| BOM | Bill of Materials - raw components needed to produce a finished product |
| Lead Time | Days between purchase order placement and material arrival |
| Manufacturing Order | Customer demand for a specific quantity of finished goods |
| Purchase Order | Request to supplier for materials to replenish inventory |
| SimDay | A single iteration of the simulation cycle |
| Stockout | Situation where inventory reaches zero while demand exists |

---

## 15. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Project Owner | ________________ | ________ | _________ |
| Technical Lead | ________________ | ________ | _________ |
| QA Lead | ________________ | ________ | _________ |
