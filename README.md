# 3D Printer Supply Chain Simulator

Multi-agent supply chain simulation across Weeks 5–8 of the DGSI course.
Three independent FastAPI services (provider, manufacturer, retailer) share
a simulated world over REST. A turn engine advances them day-by-day, injects
market signals from scenario files, and invokes a Claude Code skill per role
each day.

> Deterministic plumbing hosts non-deterministic strategy: Python apps and a
> turn engine handle execution; LLM agents (or a deterministic mock) drive
> the daily decisions.

See [docs/PRD.md](docs/PRD.md) for the full architecture and contract.

## Prerequisites

- Python 3.11+
- (Optional) [`claude` CLI](https://docs.claude.com/en/docs/claude-code/cli)
  on `PATH` to drive agents with real LLM calls. Without it the engine falls
  back to `mock_agent.py`.

## Setup

```bash
git clone https://github.com/3LVcT50r/DGSI-Lab5.git
cd DGSI-Lab5

# Create and activate a virtualenv (Linux / macOS)
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Run the three services

Open three terminals (or use a multiplexer like `tmux`). Activate the venv
in each.

```bash
# Terminal 1
cd provider-app && PYTHONPATH=. python -m src.cli serve --port 8001

# Terminal 2
cd factory-app && PYTHONPATH=. python -m src.cli serve --port 8002

# Terminal 3
cd retailer-app && PYTHONPATH=. python -m src.cli serve --port 8003
```

Health check:

```bash
curl http://localhost:8001/api/v1/catalog
curl http://localhost:8002/api/v1/inventory
curl http://localhost:8003/api/v1/catalog
```

Each app also serves interactive Swagger UI at `http://localhost:<port>/docs`.

## Run one full simulation

From the project root (with all three services up):

```bash
# Calm 25-day baseline (control group)
python turn_engine.py config/sim.json scenarios/calm-market.json 25 \
    --seed 1 --run-tag calm

# Reset the DBs between runs so the next scenario starts clean
curl -X POST http://localhost:8001/api/v1/day/reset
curl -X POST http://localhost:8002/api/v1/simulate/reset
# (retailer has no reset endpoint yet — delete its .sqlite file and restart
# the retailer process, or use POST /api/v1/state/import to reseed.)

# Volatile 25-day run (Black Friday + chip shortage + Christmas)
python turn_engine.py config/sim.json scenarios/holiday-rush.json 25 \
    --seed 1 --run-tag holiday
```

`--run-tag NAME` archives the three SQLite DBs into `runs/<NAME>/` so they
can be re-analysed later without colliding with the next run.

Force the deterministic mock agent (no LLM cost, no `claude` CLI required):

```bash
# Linux / macOS
FORCE_MOCK_AGENT=1 python turn_engine.py config/sim.json scenarios/smoke-test.json 3

# Windows PowerShell
$env:FORCE_MOCK_AGENT = "1"
python turn_engine.py config\sim.json scenarios\smoke-test.json 3
```

## Analyse a run

```bash
# Charts for whichever run is currently in the live DBs
python analyze_sim.py scenarios/holiday-rush.json --out reports/holiday-rush

# Charts for an archived run
python analyze_sim.py scenarios/holiday-rush.json \
    --db-dir runs/holiday --out reports/holiday-rush
```

Writes four PNGs under `reports/holiday-rush/`:

- `inventory_over_time.png` — three lines: parts @ manufacturer, finished
  printers @ manufacturer, printers @ retailer; with shaded event bands.
- `prices_over_time.png` — provider top-tier, manufacturer wholesale,
  retailer retail; with shaded event bands.
- `order_fulfillment.png` — per-day grouped bars: placed / fulfilled /
  backordered.
- `events_strip.png` — standalone scenario-events strip.

## Compare two scenarios

After running both with `--run-tag`:

```bash
python compare_scenarios.py \
    --run-a runs/calm    --scenario-a scenarios/calm-market.json   --label-a "Calm" \
    --run-b runs/holiday --scenario-b scenarios/holiday-rush.json  --label-b "Holiday" \
    --out reports/calm-vs-holiday
```

Produces side-by-side `inventory_compare.png`, `prices_compare.png`,
`fulfillment_compare.png`.

## Project layout

```
DGSI-Lab5/
├── provider-app/          # Parts provider (:8001)
├── factory-app/           # Manufacturer (:8002)
├── retailer-app/          # Retail store (:8003)
├── skills/                # *.md — one skill per role
├── scenarios/             # *.json — calm-market, holiday-rush, smoke-test
├── config/sim.json        # Engine config: app URLs + skill paths
├── logs/                  # day-NNN-role.log (gitignored)
├── runs/                  # Archived SQLite snapshots, per --run-tag
├── reports/               # Generated PNGs from analyze_sim / compare_scenarios
├── docs/
│   ├── PRD.md             # Full system requirements
│   └── report.md          # Final 5–8 page Week 8 report
├── turn_engine.py
├── mock_agent.py
├── analyze_sim.py
├── compare_scenarios.py
├── provider-cli / .cmd    # Bash + Windows CLI wrappers
├── manufacturer-cli / .cmd
├── retailer-cli / .cmd
└── requirements.txt
```

## Troubleshooting

- **`ModuleNotFoundError: No module named 'pydantic_settings'`** — the
  `python` on your `PATH` is not the venv interpreter. Activate the venv
  first, or invoke the apps via the venv's python directly:
  `./.venv/bin/python -m src.cli serve --port 8001` on Linux,
  `.\.venv\Scripts\python.exe -m src.cli serve --port 8001` on Windows.
- **`sqlite3.OperationalError: database is locked`** — the apps default to
  `uvicorn --reload`, which spawns two processes sharing the same SQLite
  file. For long simulations, prefer running without reload (currently this
  means accepting the contention or running each app with a single process).
- **`Day N: 0 placed / 0 fulfilled ...`** — either the retailer agent isn't
  acting (check `logs/day-NNN-retailer-*.log`) or the scenario's `base_demand`
  is too low.
- **Old SQLite files from a previous schema** — Week 8 added new tables
  (`signal_state`, `metrics`). If you see `OperationalError: no such table`
  errors, delete `*/data/*.sqlite` and restart the services to recreate the
  schema from `Base.metadata.create_all`.

## License & credits

Coursework project for DGSI. Built with FastAPI, SQLAlchemy, matplotlib,
and Claude Code.
