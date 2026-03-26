# Product Requirements Document: 3D Printer Production Simulator

## What This Is

A production-grade simulation system that models a 3D printing farm environment. The simulator creates realistic printer behaviors, job queues, material consumption, and failure scenarios to test monitoring systems, validate scheduling algorithms, train operators, and perform load testing on backend APIs without requiring physical hardware.

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Language** | Python 3.11+ | Strong typing, rich ecosystem for simulation & APIs |
| **API Framework** | FastAPI + Pydantic | Async support, auto OpenAPI docs, validation |
| **Dashboard UI** | Streamlit | Rapid development, real-time updates, charts built-in |
| **Database** | SQLite + SQLAlchemy | Zero-config, portable, easy testing, scales to medium load |
| **Simulation Engine** | SimPy | Proven discrete-event simulation, handles concurrent processes |
| **Charts/Visualization** | matplotlib | Flexible, Streamlit-compatible via `st.pyplot()` |
| **Task Queue** | asyncio + internal queue | Built-in, sufficient for simulated workloads |
| **Config Management** | pydantic-settings | Type-safe env var/config file management |

---

## Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐         ┌─────────────────────────┐   │
│  │   Streamlit Dashboard│         │     REST API (FastAPI)  │   │
│  │  - Real-time status  │         │  - Job management       │   │
│  │  - Printer visuals   │         │  - Configuration        │   │
│  │  - Analytics charts  │         │  - Simulation controls  │   │
│  └──────────┬───────────┘         └──────────┬──────────────┘   │
└─────────────┼────────────────────────────────┼──────────────────┘
              │                                │
              ▼                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ Job Service      │  │ Printer Service  │  │ SimEngine     │  │
│  │ - Queue mgmt     │  │ - Status tracking│  │ - SimPy core  │  │
│  │ - Scheduling     │  │ - Assignment     │  │ - Time control│  │
│  │ - Priority logic │  │ - Failure inject │  │ - Event hooks │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
│  ┌──────────────────┐  ┌─────────────────────────────────────┐  │
│  │ Material Service │  │ Notification Service                │  │
│  │ - Inventory      │  │ - Alerts, webhooks, logging         │  │
│  │ - Consumption    │  │                                     │  │
│  └──────────────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  SQLite Database (SQLAlchemy ORM)                       │    │
│  │  - printers, jobs, materials, events, logs              │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architecture Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| **Simulation paradigm** | Discrete-event (SimPy) | Natural fit for print jobs, failures, maintenance as events |
| **Sync vs Async API** | Async (asyncio) | Handles concurrent printer polling, dashboard updates efficiently |
| **State storage** | Relational (SQLite) | Complex queries, relationships, ACID guarantees for auditability |
| **Separation of concerns** | Service layer pattern | Business logic decoupled from API routes, testable in isolation |
| **Time model** | Simulated time (SimPy) | Can speed up/slow down simulation, replay scenarios deterministically |

### Simulation Design

```python
# Core simulation flow
class PrintJobSimulator:
    """Simulates a single print job lifecycle."""

    phases = [
        "preheat",           # 2-5 min
        "print_layer",       # Repeated per layer
        "cool_down",         # 5-15 min
        "remove_part"        # Manual simulation
    ]

    failure_points = [
        ("spool_runout", 0.02),      # 2% chance per job
        ("bed_adhesion", 0.03),      # 3% chance at start
        ("hotend_clog", 0.01),       # 1% chance mid-print
        ("power_interrupt", 0.005)   # 0.5% chance anytime
    ]
```

---

## Data Model

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    Printer      │       │     Job         │       │   FilamentSpool │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │──────<│ id (PK)         │       │ id (PK)         │
│ name            │       │ printer_id(FK) >│       │ name            │
│ model           │       │ status          │       │ material_type   │
│ status          │       │ priority        │       │ color           │
│ bed_size_x      │       │ estimated_time  │       │ weight_grams    │
│ bed_size_y      │       │ actual_time     │       │ price_per_kg    │
│ bed_size_z      │       │ spool_id(FK) >  │       │ provider        │
│ temperature     │       │ started_at      │       │ created_at      │
│ last_maintenance│       │ completed_at    │       └─────────────────┘
│ firmware_version│       │ failure_reason  │
│ created_at      │       │ progress_pct    │
│ updated_at      │       │ gcode_file_path │
└─────────────────┘       │ metadata(JSON)  │
        │                 └─────────────────┘
        │                         │
        │                         │ consumes
        │                         ▼
        │                 ┌─────────────────┐
        │                 │  MaterialUsage  │
        │                 ├─────────────────┤
        │                 │ id (PK)         │
        │                 │ job_id (FK)     │
        │                 │ spool_id (FK)   │
        │                 │ grams_used      │
        │                 │ timestamp       │
        │                 └─────────────────┘
        │
        │                 ┌─────────────────┐
        └────────-------->|   Maintenance   │
                          ├─────────────────┤
                          │ id (PK)         │
                          │ printer_id (FK) │
                          │ type            │
                          │ scheduled_at    │
                          │ completed_at    │
                          │ notes           │
                          └─────────────────┘
```

### Core Entities

#### Printer
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | string | Human-readable name (e.g., "Prusa-MK4-01") |
| `model` | string | Printer model |
| `status` | enum | `idle`, `printing`, `paused`, `error`, `maintenance` |
| `bed_size` | tuple | (x, y, z) in mm |
| `current_temp` | float | Hotend temperature |
| `bed_temp` | float | Heated bed temperature |
| `current_job_id` | FK | Reference to active job |
| `firmware_version` | string | Firmware version |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

#### Job
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | string | Job/display name |
| `printer_id` | FK | Assigned printer (nullable until assigned) |
| `status` | enum | `queued`, `assigned`, `printing`, `paused`, `completed`, `failed`, `cancelled` |
| `priority` | int | 1-10, higher = more urgent |
| `estimated_duration_min` | int | Estimated print time |
| `actual_duration_min` | int | Actual time (populated on completion) |
| `spool_id` | FK | Filament spool reference |
| `layer_height` | float | Slice setting |
| `infill_percentage` | int | Slice setting |
| `support_material` | bool | Slice setting |
| `started_at` | datetime | When printing began |
| `completed_at` | datetime | When finished |
| `failure_reason` | string | If failed, reason code |
| `progress_percent` | float | 0-100 current progress |
| `gcode_metadata` | JSON | Layer count, filament length, etc. |

#### FilamentSpool
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | string | Spool identifier |
| `material_type` | enum | `PLA`, `PETG`, `ABS`, `TPU`, etc. |
| `color` | string | Color name or hex code |
| `initial_weight_grams` | int | Original weight |
| `remaining_weight_grams` | int | Current weight |
| `price_per_kg` | float | Cost reference |
| `provider` | string | Manufacturer/vendor |
| `created_at` | datetime |入库 timestamp |

#### MaintenanceRecord
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `printer_id` | FK | Which printer |
| `type` | enum | `calibration`, `nozzle_replace`, `bed_level`, `lubrication`, `other` |
| `scheduled_at` | datetime | Planned date |
| `completed_at` | datetime | Actual completion |
| `duration_min` | int | How long it took |
| `notes` | text | Technician notes |

#### SimulationEvent (Audit Log)
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `timestamp` | datetime | When event occurred |
| `event_type` | string | Job started, printer error, etc. |
| `entity_type` | string | printer, job, material |
| `entity_id` | UUID | Affected entity |
| `details` | JSON | Event-specific data |
| `sim_time` | float | SimPy simulation time |

---

## API Endpoints

### Base URL: `/api/v1`

#### Printers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/printers` | List all printers with pagination |
| POST | `/printers` | Create a new printer |
| GET | `/printers/{id}` | Get printer details |
| PUT | `/printers/{id}` | Update printer configuration |
| DELETE | `/printers/{id}` | Remove printer |
| POST | `/printers/{id}/pause` | Pause current job |
| POST | `/printers/{id}/resume` | Resume paused job |
| POST | `/printers/{id}/cancel` | Cancel current job |
| GET | `/printers/{id}/history` | Job history for printer |

#### Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/jobs` | List jobs with filters (status, priority) |
| POST | `/jobs` | Create new print job |
| GET | `/jobs/{id}` | Get job details |
| PUT | `/jobs/{id}` | Update job (priority, assignment) |
| DELETE | `/jobs/{id}` | Cancel/remove job |
| POST | `/jobs/{id}/assign` | Assign to printer |
| GET | `/jobs/{id}/progress` | Get live progress |

#### Materials / Filament
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/materials/spools` | List all spools |
| POST | `/materials/spools` | Add new spool |
| GET | `/materials/spools/{id}` | Get spool details |
| PUT | `/materials/spools/{id}` | Update spool info |
| GET | `/materials/usage` | Usage history |

#### Simulation Control
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/simulation/start` | Start/resume simulation |
| POST | `/simulation/pause` | Pause simulation |
| POST | `/simulation/stop` | Stop simulation |
| GET | `/simulation/status` | Current sim state |
| POST | `/simulation/time-scale` | Set sim speed (0.5x, 1x, 10x, etc.) |
| POST | `/simulation/inject-failure` | Manually inject failure scenario |
| GET | `/simulation/events` | Event log |

#### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/farm-utilization` | Overall utilization metrics |
| GET | `/analytics/job-stats` | Completion rates, avg times |
| GET | `/analytics/material-consumption` | Filament usage reports |
| GET | `/analytics/maintenance-schedule` | Upcoming/completed maintenance |

### Example Request/Response

**POST /api/v1/jobs**
```json
// Request
{
  "name": "Prototype-Casing-V3",
  "priority": 7,
  "estimated_duration_min": 180,
  "spool_id": "uuid-of-spool",
  "layer_height": 0.2,
  "infill_percentage": 20,
  "gcode_metadata": {
    "layer_count": 950,
    "filament_length_mm": 4200,
    "file_size_mb": 8.4
  }
}

// Response 201
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Prototype-Casing-V3",
  "status": "queued",
  "priority": 7,
  "created_at": "2026-03-26T10:30:00Z",
  "queue_position": 3
}
```

---

## Streamlit Dashboard Views

### 1. **Overview Dashboard**
- Farm utilization gauge
- Active printers grid with status indicators
- Jobs in progress cards
- Alerts/errors banner

### 2. **Printer Detail View**
- Selected printer status panel
- Temperature graph (real-time)
- Current job progress bar
- Control buttons (pause, resume, cancel)

### 3. **Job Queue Manager**
- Sortable/filterable job table
- Drag-and-drop reordering (priority)
- Bulk actions (assign, cancel)
- Queue analytics sidebar

### 4. **Materials Inventory**
- Spool list with remaining % gauges
- Low-stock alerts
- Material consumption charts
- Cost analysis view

### 5. **Analytics Report**
- Utilization trends over time
- Print success/failure rate
- Average print duration histogram
- Material cost per period

### 6. **Simulation Controls**
- Start/stop/pause controls
- Speed multiplier slider
- Scenario picker (pre-configured)
- Failure injection panel

---

## Coding Conventions

- **Type hints everywhere** — Use explicit types for all function signatures
- **Pydantic models for schemas** — All API request/response validated through Pydantic
- **Service-layer separation** — API routes contain only HTTP logic; business logic in services
- **Docstrings** — Google-style docstrings for public functions/classes
- **Configuration** — All settings via `.env` or `config.yaml` using pydantic-settings
- **Logging** — Structured logging with context (sim_time, entity_id)
- **Testing** — pytest with coverage; unit tests for services, integration tests for API

### Project Structure
```
src/
├── api/
│   ├── __init__.py
│   ├── routers/
│   │   ├── printers.py
│   │   ├── jobs.py
│   │   ├── materials.py
│   │   ├── simulation.py
│   │   └── analytics.py
│   └── dependencies.py
├── services/
│   ├── __init__.py
│   ├── printer_service.py
│   ├── job_service.py
│   ├── material_service.py
│   └── notification_service.py
├── simulation/
│   ├── __init__.py
│   ├── engine.py
│   ├── processes.py
│   └── scenarios.py
├── models/
│   ├── __init__.py
│   ├── database.py
│   ├── printer.py
│   ├── job.py
│   └── material.py
├── schemas/
│   ├── __init__.py
│   ├── printer.py
│   ├── job.py
│   └── material.py
├── config/
│   ├── settings.py
│   └── default.yaml
├── utils/
│   ├── __init__.py
│   └── helpers.py
└── main.py

dashboard/
├── app.py
├── pages/
│   ├── 1_Printers.py
│   ├── 2_Jobs.py
│   ├── 3_Materials.py
│   ├── 4_Analytics.py
│   └── 5_Simulation.py
└── components/
    └── printer_card.py

tests/
├── unit/
├── integration/
└── fixtures/

requirements.txt
README.md
.env.example
PRD.md
```

---

## Development Plan

### Phase 1: Foundation (Week 1)
**Goal:** Working API with basic CRUD, database models, and project scaffolding

| Task | Deliverable | Est. Days |
|------|-------------|-----------|
| Setup project structure | Initialized repo with folder layout, requirements | 0.5 |
| Database models | SQLAlchemy models for Printer, Job, Spool | 1 |
| API skeleton | FastAPI app, dependency injection, error handling | 0.5 |
| Printer CRUD endpoints | Full Create/Read/Update/Delete for printers | 1 |
| Job CRUD endpoints | Full Create/Read/Update/Delete for jobs | 1 |
| Material CRUD endpoints | Full Create/Read/Update/Delete for spools | 1 |
| Unit tests | >80% coverage on models and services | 1 |

**Milestone 1:** Basic API operational, can create/print jobs manually

---

### Phase 2: Simulation Core (Week 2)
**Goal:** SimPy-based simulation engine driving printer states

| Task | Deliverable | Est. Days |
|------|-------------|-----------|
| SimPy environment setup | Simulation core with time control | 0.5 |
| Printer simulation process | State machine (idle→printing→completed/error) | 1.5 |
| Job processing logic | Queue assignment, priority handling | 1 |
| Failure injection system | Random/manual failure generation | 1 |
| Progress tracking | Real-time progress percentage updates | 0.5 |
| Integration with API | Connect sim events to API state | 0.5 |
| Tests for simulation | Deterministic test scenarios | 1 |

**Milestone 2:** Simulation running independently, printers transition states realistically

---

### Phase 3: Dashboard MVP (Week 3)
**Goal:** Streamlit UI for monitoring and basic interaction

| Task | Deliverable | Est. Days |
|------|-------------|-----------|
| Dashboard scaffold | Streamlit app with navigation | 0.5 |
| Overview page | Farm status grid, quick stats | 1 |
| Printer detail page | Individual printer view + controls | 1 |
| Job queue page | Table with filtering/sorting | 1 |
| Real-time polling/updates | Auto-refresh mechanism | 0.5 |
| Styling/theming | Consistent visual design | 0.5 |

**Milestone 3:** Users can monitor simulation progress via UI

---

### Phase 4: Advanced Features (Week 4)
**Goal:** Materials, analytics, and simulation controls

| Task | Deliverable | Est. Days |
|------|-------------|-----------|
| Material consumption logic | Track filament usage per job | 1 |
| Materials dashboard page | Spool inventory view | 1 |
| Analytics API endpoints | Aggregation queries | 1 |
| Analytics dashboard page | Charts and reports | 1 |
| Simulation controls UI | Speed, start/stop, scenarios | 0.5 |
| Failure injection UI | Manual trigger interface | 0.5 |

**Milestone 4:** Feature-complete simulator

---

### Phase 5: Polish & Documentation (Week 5)
**Goal:** Production-ready quality

| Task | Deliverable | Est. Days |
|------|-------------|-----------|
| Integration tests | End-to-end workflow tests | 1 |
| Performance optimization | Handle 100+ concurrent printers | 1 |
| Error handling polish | User-friendly messages, logging | 0.5 |
| API documentation | Swagger refinement, examples | 0.5 |
| README & setup guide | Quickstart for new users | 0.5 |
| Sample data/scenarios | Pre-loaded demo content | 0.5 |
| Final review & refactor | Code quality pass | 1 |

**Milestone 5:** Release v1.0

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SimPy learning curve | Medium | Spike study in Week 1, use example scenarios |
| Streamlit real-time performance | Medium | Implement efficient polling, consider WebSockets if needed |
| Simulation accuracy expectations | High | Document assumptions, make parameters configurable |
| Scope creep (additional features) | Medium | Stick to MVP scope, backlog non-critical items |

---

## Open Questions / TODOs

- [ ] Confirm expected scale: How many printers should be simulatable? (affects DB choice)
- [ ] Define failure scenarios in detail (what percentages, what recovery?)
- [ ] Should G-code files be parsed or is metadata enough?
- [ ] Multi-user support? Or single-session simulator?
- [ ] Export capabilities needed? (CSV reports, PDF summaries)
- [ ] Authentication required for API/dashboard?

---

## Glossary

| Term | Definition |
|------|------------|
| **SimPy** | Python library for discrete-event simulation |
| **Discrete-event simulation** | System modeled as sequence of events at specific times |
| **Spool** | A roll of 3D printing filament |
| **G-code** | Instructions sent to 3D printer for execution |
| **Utilization** | Percentage of time printer spends actively printing |

---

*Document Version: 1.0 Draft*
*Created: 2026-03-26*
*Author: AI Assistant*
*Status: Pending Review*
