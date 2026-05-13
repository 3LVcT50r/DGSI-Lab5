# Week 7: The Supply Chain (Part 2) — Retailer & Turn Engine — Implementation Status

## Completed This Week ✅

### 1. **Retailer App (retailer-app/)** — COMPLETE
   - Full FastAPI REST server on port 8003
   - SQLite database with 6 entity models:
     - `Product` — Printer models with wholesale/retail prices
     - `CustomerOrder` — End-customer orders (pending → fulfilled → backordered)
     - `PurchaseOrder` — Wholesale orders to manufacturer
     - `Stock` — Inventory tracking
     - `SimState` — Day counter singleton
     - `Event` — Audit trail
   
   - **API Endpoints (all `/api/v1`)**:
     - `GET /catalog` — Product catalog with retail prices
     - `GET /stock` — Current inventory
     - `POST /orders` — Accept customer order (from demand engine)
     - `GET /orders` — List customer orders (filterable by status)
     - `GET /orders/{id}` — Order details
     - `POST /orders/{id}/fulfill` — Ship from stock
     - `POST /orders/{id}/backorder` — Mark as waiting
     - `POST /purchases` — Order from manufacturer
     - `GET /purchases` — List wholesale purchase orders
     - `POST /day/advance` — Advance one day (auto-fulfill backorders)
     - `GET /day/current` — Current day
     - `GET /events` — Audit trail
   
   - **CLI Commands** (`./retailer-cli`):
     - `catalog` — Show models and prices
     - `stock` — Show inventory
     - `customers orders [--status]` — List customer orders
     - `customers order <id>` — Show order details
     - `customers fulfill <id>` — Fulfill from stock
     - `customers backorder <id>` — Mark as backordered
     - `purchase list` — Show wholesale POs
     - `purchase create --model <name> --qty <n>` — Order from manufacturer
     - `day current` — Show current day
     - `day advance` — Advance day
     - `serve --port 8003` — Start server

---

### 2. **Manufacturer App Extensions** — COMPLETE
   - Added `SalesOrder` model to track retailer orders
   - Added `SalesOrderStatus` enum (pending → released → completed)
   - New API endpoint: `POST /api/v1/sales-orders` — Accept retailer order
   - New CLI command: `./manufacturer-cli sales orders` — List retailer orders
   - Manufacturer now listens for inbound retailer orders via REST

---

### 3. **Turn Engine** (`turn_engine.py`) — COMPLETE
   - **Command**: `python turn_engine.py config/sim.json scenarios/smoke-test.json 3`
   - **Flow per day**:
     1. Load scenario signals (demand modifier, events)
     2. Generate customer demand → POST to retailers
     3. Run retailer agent (if skill exists, else stub)
     4. Run manufacturer agent (if skill exists, else stub)
     5. Run provider agent (if skill exists, else stub)
     6. Advance all three apps to next day
   
   - **Features**:
     - Reads turn sequence from config
     - Logs all agent output to `logs/day-{N}-{role}.log`
     - Graceful timeouts (180s per agent)
     - Supports both agent-mode and stub-mode
     - Scenario file controls demand modifiers and special events

---

### 4. **Config & Scenario Files** — COMPLETE
   - **`config/sim.json`**: Defines all three apps, ports, working dirs, and optional skill files
   - **`scenarios/smoke-test.json`**: Minimal scenario with steady demand (mean=4) over 10 days

---

### 5. **First Skill Files** — COMPLETE
   - **`skills/manufacturer-manager.md`** (192 lines):
     - Teaches the agent to assess stock, release orders, replenish parts, and adjust prices
     - Explicit "DO NOT" section (forbids `day advance`, invalid commands, overfulfillment)
     - Decision framework with clear steps
     - Requires summary output at end
   
   - **`skills/retailer-manager.md`** (175 lines):
     - Teaches the agent to fulfill orders, backorder when needed, and replenish inventory
     - Enforces 15% minimum markup constraint
     - Clear command mappings
     - Summary output required

---

### 6. **Project Structure**
   ```
   DGSI-Lab5/
   ├── retailer-app/                # NEW: Retail storefront app
   │   ├── src/
   │   │   ├── main.py              # FastAPI entry point
   │   │   ├── cli.py               # Command-line interface
   │   │   ├── models/              # ORM: Product, CustomerOrder, PurchaseOrder, Stock, Event
   │   │   ├── schemas/             # Request/response DTOs
   │   │   ├── services/            # Business logic
   │   │   └── api/                 # REST routes
   │   └── data/seed-retailer.json
   ├── factory-app/                 # EXTENDED: Manufacturer accepts retailer orders
   │   ├── src/
   │   │   ├── models/order.py      # Added SalesOrder
   │   │   ├── api/sales.py         # NEW: Sales order endpoints
   │   │   └── services/sales.py    # NEW: Sales logic
   ├── provider-app/                # Unchanged
   ├── turn_engine.py               # NEW: Main orchestrator script
   ├── config/
   │   └── sim.json                 # NEW: Engine configuration
   ├── scenarios/
   │   └── smoke-test.json          # NEW: Minimal test scenario
   ├── skills/
   │   ├── manufacturer-manager.md  # NEW: Agent skill for factory
   │   └── retailer-manager.md      # NEW: Agent skill for retail
   ├── retailer-cli                 # NEW: CLI wrapper (Linux/macOS)
   ├── retailer-cli.cmd             # NEW: CLI wrapper (Windows)
   └── logs/                        # NEW: Agent output logs
   ```

---

## Testing Checklist ✅

- [x] All three apps start on their own ports (8003, 8002, 8001)
- [x] Retailer CLI works: `catalog`, `stock`, `customers orders`, `purchase list`, `day current`
- [x] Manufacturer accepts retailer orders via `POST /api/v1/sales-orders`
- [x] Turn engine runs 3 deterministic (stub) days without errors
- [x] Config and scenario files load correctly
- [x] Skill files exist and contain complete decision frameworks
- [x] All required CLI commands are present and documented

---

## Running the Full System

### 1. **Start all three servers** (three separate terminals):
   ```bash
   ./manufacturer-cli serve --port 8002
   ./provider-cli serve --port 8001
   ./retailer-cli serve --port 8003
   ```

### 2. **Run the turn engine** (deterministic, stub mode):
   ```bash
   python turn_engine.py config/sim.json scenarios/smoke-test.json 3
   ```
   Expected output:
   - Customer demand generated
   - Stubs log that retail/mfg/provider would make decisions
   - All apps advance to day 2, 3

### 3. **Inspect the logs**:
   ```bash
   cat logs/day-*-*.log
   ```

---

## Next Steps (Week 8)

1. **Make one agent live**: Point `config/sim.json` at the manufacturer skill
   ```json
   "skill": "skills/manufacturer-manager.md"
   ```

2. **Run with agent active**:
   ```bash
   python turn_engine.py config/sim.json scenarios/smoke-test.json 1
   ```
   The manufacturer will now read its skill and make real decisions

3. **Iterate**: If the agent behaves poorly, rewrite the skill (not the agent code)

4. **Repeat for retailer**: Once manufacturer works, activate retailer skill and test

5. **Document**:
   - Skill effectiveness (what worked, what failed)
   - Agent logs (pasted into report)
   - Edge cases discovered
   - Vibe-coding observations (Claude Code vs. agent)

---

## Known Limitations

- **Demand generation is deterministic** (not yet parameterized by price elasticity)
- **Agents can only run with `claude --print`** (must have Claude Code installed locally)
- **No distributed coordination** yet (agents operate independently; Week 8 will refine)
- **Price adjustments not yet enforced** in retailer service layer (manual validation only)

---

## Files Added This Week

| File | Lines | Purpose |
|------|-------|---------|
| `retailer-app/src/main.py` | 41 | FastAPI boot |
| `retailer-app/src/cli.py` | 430 | CLI parser & commands |
| `retailer-app/src/database.py` | 24 | SQLite config |
| `retailer-app/src/models/*.py` | 150 | ORM models |
| `retailer-app/src/schemas/*.py` | 95 | Pydantic DTOs |
| `retailer-app/src/services/retailer.py` | 280 | Business logic |
| `retailer-app/src/api/*.py` | 150 | REST routes |
| `factory-app/src/api/sales.py` | 45 | Sales order endpoints |
| `factory-app/src/services/sales.py` | 35 | Sales logic |
| `factory-app/src/models/order.py` | +50 | SalesOrder model |
| `turn_engine.py` | 210 | Orchestration script |
| `skills/manufacturer-manager.md` | 192 | Manufacturer skill |
| `skills/retailer-manager.md` | 175 | Retailer skill |
| `config/sim.json` | 20 | Engine config |
| `scenarios/smoke-test.json` | 12 | Test scenario |
| **Total** | ~1700 | Week 7 deliverables |

---

## Key Design Decisions

1. **Retailer as a separate app** (not embedded): Allows independent testing, scaling, multi-instance scenarios
2. **Skill files in markdown**: Human-readable, easy to iterate, Claude can read and execute instructions reliably
3. **Turn engine in Python**: Fast prototyping, easy to debug agent subprocess calls
4. **Logs stored to disk**: Persistent audit trail for analysis
5. **Deterministic first, agents second**: Smoke test validates plumbing before LLM agents enter
6. **Order-of-operations deliberate**: Retailers decide first (demand), then manufacturer (production), then provider (supply)

---

## Proof of Concept: Ready ✅

All plumbing in place. Next week: activate agents and iterate on skills based on observed behavior.