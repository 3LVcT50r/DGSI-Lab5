#!/usr/bin/env python3
"""Turn engine: orchestrates one simulated day across all apps."""

import subprocess
import json
import httpx
import logging
from pathlib import Path
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    return json.loads(Path(path).read_text())


def load_scenario(path: str) -> Dict[str, Any]:
    """Load scenario from JSON file."""
    return json.loads(Path(path).read_text())


def todays_signal(day: int, scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Extract market signal for today from scenario."""
    signal = {"day": day, "events": []}
    for event in scenario.get("events", []):
        if event["start_day"] <= day <= event["end_day"]:
            signal["events"].append(event)
    
    signal["demand_modifier"] = 1.0
    for event in signal.get("events", []):
        signal["demand_modifier"] = event.get("demand_modifier", 1.0)
    
    signal.setdefault("demand_modifier", 1.0)
    signal["base_demand"] = scenario.get("base_demand", {"mean": 5, "variance": 2})
    return signal


def generate_customer_orders(retailer_url: str, retailer_name: str, signal: Dict[str, Any]) -> None:
    """Generate and POST customer demand to a retailer."""
    import random
    
    base = signal.get("base_demand", {"mean": 5, "variance": 2})
    modifier = signal.get("demand_modifier", 1.0)
    
    # Get catalog from retailer
    try:
        response = httpx.get(f"{retailer_url}/api/v1/catalog")
        response.raise_for_status()
        catalog = response.json()
    except Exception as exc:
        logger.warning(f"Failed to get catalog from {retailer_url}: {exc}")
        return
    
    # Generate orders for each model
    for item in catalog:
        mean_orders = base["mean"] * modifier
        # Simple demand: ignore price factor for now
        n = max(0, int(random.gauss(mean_orders, base.get("variance", 1))))
        
        for _ in range(n):
            payload = {
                "customer_name": "auto",
                "product_name": item["name"],
                "quantity": 1
            }
            try:
                httpx.post(f"{retailer_url}/api/v1/orders", json=payload)
            except Exception as exc:
                logger.warning(f"Failed to post order to {retailer_url}: {exc}")


def run_agent_or_stub(role: str, skill_path: str | None, context: str, app_working_dir: str, url: str) -> None:
    """Run an agent using the python mock agent script."""
    try:
        import sys
        import os
        mock_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mock_agent.py"))
        result = subprocess.run(
            [sys.executable, mock_path, role, url, context],
            cwd=app_working_dir,
            capture_output=True,
            text=True,
            timeout=180,
        )
        logger.info(f"[{role}] Agent output:\n{result.stdout}")
        
        # Save output to log file
        try:
            day_num = json.loads(context).get("day", 0)
            log_path = Path("logs") / f"day-{day_num}-{role}.log"
            log_path.write_text(result.stdout)
        except Exception:
            pass
            
        if result.stderr:
            logger.warning(f"[{role}] Agent stderr:\n{result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error(f"[{role}] Agent timeout (180s)")
    except Exception as exc:
        logger.error(f"[{role}] Agent failed: {exc}")


def advance_all(config: Dict[str, Any]) -> None:
    """Advance all apps to the next day."""
    urls_with_endpoints = []
    for r in config.get("retailers", []):
        urls_with_endpoints.append((r["url"], "/api/v1/day/advance"))
    
    manuf = config.get("manufacturer")
    if manuf:
        urls_with_endpoints.append((manuf["url"], "/api/v1/simulate/advance"))
        
    for p in config.get("providers", []):
        urls_with_endpoints.append((p["url"], "/api/v1/day/advance"))

    for url, endpoint in urls_with_endpoints:
        try:
            resp = httpx.post(f"{url}{endpoint}")
            if resp.status_code >= 400:
                logger.error(f"Error advancing {url}: {resp.status_code} {resp.text}")
            resp.raise_for_status()
        except Exception as exc:
            logger.warning(f"Failed to advance {url}: {exc}")


def run_day(day: int, config: Dict[str, Any], scenario: Dict[str, Any]) -> None:
    """Execute one full simulated day."""
    signal = todays_signal(day, scenario)
    logger.info(f"\n{'='*60}\n DAY {day} signal={signal}\n{'='*60}")
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # 1. Generate customer demand at retailers
    for retailer in config["retailers"]:
        logger.info(f"Generating customer demand for {retailer['name']}")
        generate_customer_orders(retailer["url"], retailer["name"], signal)
    
    # 2. Run retailer agents
    context_json = json.dumps(signal)
    for retailer in config["retailers"]:
        logger.info(f"Running retailer agent: {retailer['name']}")
        run_agent_or_stub(
            f"retailer-{retailer['name']}",
            retailer.get("skill"),
            context_json,
            retailer["path"],
            retailer["url"]
        )
    
    # 3. Run manufacturer agent
    logger.info("Running manufacturer agent")
    manuf = config["manufacturer"]
    run_agent_or_stub(
        "manufacturer",
        manuf.get("skill"),
        context_json,
        manuf["path"],
        manuf["url"]
    )
    
    # 4. Run provider agents
    for provider in config["providers"]:
        logger.info(f"Running provider agent: {provider['name']}")
        run_agent_or_stub(
            f"provider-{provider['name']}",
            provider.get("skill"),
            context_json,
            provider["path"],
            provider["url"]
        )
    
    # 5. Advance all apps
    logger.info("Advancing all apps to next day")
    advance_all(config)


def main() -> None:
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python turn_engine.py <config.json> <scenario.json> <num_days>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    scenario_path = sys.argv[2]
    num_days = int(sys.argv[3])
    
    config = load_config(config_path)
    scenario = load_scenario(scenario_path)
    
    for day in range(1, num_days + 1):
        run_day(day, config, scenario)


if __name__ == "__main__":
    main()