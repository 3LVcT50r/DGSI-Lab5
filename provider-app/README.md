# Provider App

A companion CLI + REST simulator for the materials provider used by the 3D printer factory app.

## Quick start

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the environment:
   - macOS / Linux:
     ```bash
     source venv/bin/activate
     ```
   - Windows PowerShell:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Run the CLI

From the `provider-app` directory:

```bash
python provider_cli.py catalog
python provider_cli.py stock
python provider_cli.py orders list
python provider_cli.py orders show 1
python provider_cli.py price set pcb 20 32
python provider_cli.py restock pcb 100
python provider_cli.py day current
python provider_cli.py day advance
python provider_cli.py export
python provider_cli.py import provider-export.json
python provider_cli.py serve --port 8001
```

## REST API

Start the service with:

```bash
python provider_cli.py serve --port 8001
```

Then use:

- `GET http://localhost:8001/api/catalog`
- `GET http://localhost:8001/api/stock`
- `POST http://localhost:8001/api/orders`
- `GET http://localhost:8001/api/orders`
- `GET http://localhost:8001/api/orders/{id}`
- `POST http://localhost:8001/api/day/advance`
- `GET http://localhost:8001/api/day/current`

## Seed data

The app initializes from `seed-provider.json` on first startup.

## Notes

- The local SQLite database is stored in `provider.db`.
- CLI commands and REST endpoints share the same business logic.
