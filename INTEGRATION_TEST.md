# Integration Test Guide: Retailer ↔ Manufacturer Flow

## Overview
This test demonstrates the full supply chain flow:
1. **Retailer** receives customer orders and depletes inventory
2. **Retailer** places purchase orders to **Manufacturer**
3. **Manufacturer** receives sales orders from retailer
4. **Manufacturer** releases orders to production
5. **Manufacturer** produces goods over several days
6. Flow continues as demand and production cycle

## Prerequisites

### 1. Start Both Apps

Choose the method that matches your platform:

#### Windows PowerShell (Two Terminals)
```powershell
# Terminal 1 - Factory
cd factory-app
python src/cli.py serve --port 8000

# Terminal 2 - Retailer (in separate PowerShell window)
cd retailer-app
python -m src.cli serve --port 8001
```

#### Linux / WSL / macOS (Two Terminals)
```bash
# Terminal 1 - Factory
cd factory-app
python -m src.cli serve --port 8000

# Terminal 2 - Retailer (in separate terminal/tmux pane)
cd retailer-app
python -m src.cli serve --port 8001
```

#### Using GNU Screen (Linux/WSL/macOS)
```bash
# Start both in background
screen -dm -S factory bash -c "cd factory-app && python -m src.cli serve --port 8000"
screen -dm -S retailer bash -c "cd retailer-app && python -m src.cli serve --port 8001"

# View specific server output
screen -r factory
# (Press Ctrl+A, then D to detach)

# Kill servers when done
screen -S factory -X quit
screen -S retailer -X quit
```

#### Using tmux (Linux/WSL/macOS)
```bash
# Create session with two panes
tmux new-session -d -s lab5 -x 200 -y 50

tmux send-keys -t lab5 "cd factory-app && python -m src.cli serve --port 8000" Enter
tmux split-window -t lab5 -h
tmux send-keys -t lab5 "cd retailer-app && python -m src.cli serve --port 8001" Enter

# View the session
tmux attach -t lab5

# Kill when done
tmux kill-session -t lab5
```

### 2. Verify Both Apps Are Running
```bash
# In another terminal
curl http://localhost:8000/health
curl http://localhost:8001/health

# Both should return {"status":"ok"} or similar
```

## Running the Test

### Option 1: Windows PowerShell (Recommended for Windows)
```powershell
cd c:\path\to\DGSI-Lab5
.\integration-test.ps1
```

### Option 2: Linux / WSL / macOS (Bash)
```bash
cd /path/to/DGSI-Lab5
chmod +x integration-test.sh
./integration-test.sh
```

### Option 3: Universal Python Runner (All Platforms)
Works on Windows, WSL, Linux, macOS:
```bash
# From workspace root
python run-integration-test.py

# With verbose output
python run-integration-test.py --verbose

# Python 3 explicit
python3 run-integration-test.py
```

## What Happens in Each Phase

### Phase 1: Initial State
- Shows current day and inventory for both apps
- Displays available catalog

### Phase 2: Retailer Advances 5 Days
- Each day, random customer orders are generated
- Stock decreases as orders are fulfilled
- Watch inventory levels drop below reorder points

**Expected Output:**
```
Order 1: customer=John, product=1, qty=5, status=fulfilled, created_day=1
Product 1: available=95, on_hold=0
...
Product 1: available=70, on_hold=0  (after 5 days)
```

### Phase 3: Retailer Creates Purchase Orders
- Retailer examines stock levels
- Creates purchase order to factory for product ID 1 (qty 30)
- Shows local purchase order record

**Expected Output:**
```
PO 1: product=1, qty=30, status=open, expected_day=6
```

### Phase 4: Factory Receives Order
- Factory CLI shows incoming **sales orders** from retailers
- This is how the two systems communicate

**Expected Output:**
```
ID: 1, Retailer: Retailer, Model: 1, Qty: 30, Status: pending
```

### Phase 5: Factory Production Planning
- Shows daily capacity (units per day)
- Shows current utilization and available capacity
- Displays raw material inventory

### Phase 6: Factory Releases Order
- Factory manager decides to release the order to production
- Manufacturing order moves from `pending` to `released` status

### Phase 7: Factory Advances 7 Days
- Each day: production progresses, materials consumed, finished goods accumulate
- Watch production completion status change

**Expected Output:**
```
ID: 1, Product: 1, Qty: 30, Status: in_progress
[next day]
ID: 1, Product: 1, Qty: 30, Status: completed
```

### Phase 8: Final State
- Compare beginning vs. end state
- Retailer: inventory replenished, PO fulfilled
- Factory: finished goods shipped, raw materials consumed

## Key Observables

| Metric | Initial | After Phase 2 | After Phase 7 |
|--------|---------|---------------|---------------|
| Retailer Inventory (P1) | ~100 | ~70 | ~100 (replenished) |
| Factory Day | 1 | 1 | 8 |
| Manufacturing Orders | 0 | 0 | 1 (completed) |
| Purchase Order Status | — | open | received |

## Troubleshooting

### Common Issues Across All Platforms

**"ModuleNotFoundError: No module named 'src'"**
- Ensure you're running from the correct app directory (factory-app or retailer-app)
- Don't run from workspace root; the test runner auto-detects and changes directories

**Apps not responding**
```bash
# Test connectivity
curl http://localhost:8000/health    # Factory
curl http://localhost:8001/health    # Retailer

# Check if ports are in use
# Windows PowerShell:
netstat -ano | findstr ":8000"
netstat -ano | findstr ":8001"

# Linux/macOS/WSL:
lsof -i :8000
lsof -i :8001
```

**No customer orders generated**
- Retailer generates 1-3 random orders per day
- Run Phase 2 multiple times if you don't see orders (randomness)

### Windows-Specific Issues

**PowerShell Execution Policy Error**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Then try again
```

**ModuleNotFoundError when running directly**
Try using the Python runner instead:
```powershell
python run-integration-test.py
```

### Linux/WSL-Specific Issues

**Permission Denied on .sh file**
```bash
chmod +x integration-test.sh
./integration-test.sh
```

**Python not found**
```bash
# Try python3 explicitly
python3 run-integration-test.py

# Or check which Python is available
which python
which python3
python --version
```

**Port already in use on WSL**
WSL and Windows may share ports. Try different ports:
```bash
# Factory on 8010, Retailer on 8011
cd factory-app && python -m src.cli serve --port 8010
cd retailer-app && python -m src.cli serve --port 8011

# Then update test script or use Python runner with env vars
```

## Advanced: Manual CLI Commands

Instead of running the full script, you can run individual commands.

### Retailer Commands

**Windows PowerShell:**
```powershell
cd retailer-app

# Show current day
python -m src.cli day current

# Advance day
python -m src.cli day advance

# List stock
python -m src.cli stock

# List customer orders
python -m src.cli customers orders

# Get specific customer order
python -m src.cli customers order 1

# Create purchase order (product_id, qty)
python -m src.cli purchase create 1 30

# List purchase orders
python -m src.cli purchase list

# Show catalog
python -m src.cli catalog

# Fulfill customer order
python -m src.cli fulfill 1
```

**Linux / WSL / Bash:**
```bash
cd retailer-app

# Show current day
python -m src.cli day current

# Advance day
python -m src.cli day advance

# List stock
python -m src.cli stock

# List customer orders
python -m src.cli customers orders

# Create purchase order (product_id, qty)
python -m src.cli purchase create 1 30

# List purchase orders
python -m src.cli purchase list

# Show catalog
python -m src.cli catalog

# Fulfill customer order
python -m src.cli fulfill 1
```

### Manufacturer Commands

**Windows PowerShell:**
```powershell
cd factory-app

# Show current day
python -m src.cli day current

# Advance day
python -m src.cli day advance

# List inventory
python -m src.cli inventory

# List incoming sales orders
python -m src.cli sales orders

# Release order to production (order_id)
python -m src.cli production release 1

# Show production status
python -m src.cli production status

# Show capacity
python -m src.cli capacity

# Set wholesale price
python -m src.cli price set "product_name" 149.99

# List wholesale prices
python -m src.cli price list
```

**Linux / WSL / Bash:**
```bash
cd factory-app

# Show current day
python -m src.cli day current

# Advance day
python -m src.cli day advance

# List inventory
python -m src.cli inventory

# List incoming sales orders
python -m src.cli sales orders

# Release order to production (order_id)
python -m src.cli production release 1

# Show production status
python -m src.cli production status

# Show capacity
python -m src.cli capacity

# Set wholesale price
python -m src.cli price set "product_name" 149.99

# List wholesale prices
python -m src.cli price list
```

## Next Steps

After running the integration test:
1. Run it again with different purchase order quantities
2. Observe how capacity constraints affect production scheduling
3. Test edge cases: over-capacity orders, backorders, stockouts
4. Export and analyze event logs: `python -m src.cli export-events`
