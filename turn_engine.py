#!/usr/bin/env python3
"""Turn engine: orchestrates one simulated day across provider, manufacturer, and retailer apps.

Per turn it:
  1. Resolves today's market signal from the scenario file.
  2. Injects deterministic customer demand into each retailer.
  3. Runs each role's agent (downstream first), either via `claude --print` if a
     skill file is configured and the CLI is available, or via the mock agent.
  4. Advances each app's simulated day via its REST API.

Per-day per-role agent stdout is persisted to logs/day-{day:03d}-{role}.log.
"""

from __future__ import annotations

import json
import logging
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_ROOT / "logs"
RUNS_DIR = PROJECT_ROOT / "runs"
AGENT_TIMEOUT_S = 180

# Source-of-truth filenames each app writes its SQLite DB to. Kept here so the
# --run-tag archive step can copy them without each tool having to know the
# layout.
APP_DB_FILES = {
    "provider": PROJECT_ROOT / "provider-app" / "data" / "provider.sqlite",
    "factory": PROJECT_ROOT / "factory-app" / "data" / "database.sqlite",
    "retailer": PROJECT_ROOT / "retailer-app" / "data" / "retailer.sqlite",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("turn_engine")


def load_config(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text())


def load_scenario(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text())


def todays_signal(day: int, scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve the market signal for `day` from the scenario.

    Overlapping events compound by taking the max of each modifier, so the most
    aggressive event in the overlap wins (e.g. christmas_season + chip_shortage).
    """
    active: List[Dict[str, Any]] = [
        event
        for event in scenario.get("events", [])
        if event.get("start_day", 1) <= day <= event.get("end_day", 1)
    ]

    signal: Dict[str, Any] = {
        "day": day,
        "events": active,
        "scenario_name": scenario.get("scenario_name", "unnamed"),
        "base_demand": scenario.get("base_demand", {"mean": 5, "variance": 2}),
        "base_price": scenario.get("base_price", 400),
        "demand_modifier": 1.0,
        "supply_modifier": 1.0,
        "lead_time_modifier": 1.0,
    }

    for event in active:
        for key in ("demand_modifier", "supply_modifier", "lead_time_modifier"):
            value = event.get(key)
            if value is not None:
                if key == "supply_modifier":
                    signal[key] = min(signal[key], value)
                else:
                    signal[key] = max(signal[key], value)
        if "price_sensitivity" in event:
            signal["price_sensitivity"] = event["price_sensitivity"]

    return signal


def generate_customer_orders(retailer: Dict[str, Any], signal: Dict[str, Any]) -> int:
    """Generate customer orders for one retailer and POST them to its API.

    Demand scales with the day's modifier. Higher prices reduce demand.
    Returns the number of orders posted (best-effort).
    """
    url = retailer["url"].rstrip("/")
    base = signal["base_demand"]
    mean = base.get("mean", 5)
    variance = base.get("variance", 2)
    modifier = signal.get("demand_modifier", 1.0)
    base_price = signal.get("base_price", 400)

    try:
        catalog = httpx.get(f"{url}/api/v1/catalog", timeout=10.0).json()
    except Exception as exc:
        logger.warning("retailer %s catalog unavailable: %s", retailer.get("name"), exc)
        return 0

    posted = 0
    for item in catalog:
        price = item.get("retail_price") or item.get("price") or base_price
        price_factor = max(0.2, 1.0 - (price - base_price) / max(base_price, 1))
        adjusted_mean = mean * modifier * price_factor
        n = max(0, int(random.gauss(adjusted_mean, max(variance, 1))))
        for _ in range(n):
            payload = {
                "customer_name": "auto",
                "product_name": item["name"],
                "quantity": 1,
            }
            try:
                httpx.post(f"{url}/api/v1/orders", json=payload, timeout=10.0)
                posted += 1
            except Exception as exc:
                logger.warning("post order to %s failed: %s", url, exc)
                break
    return posted


def _claude_available() -> bool:
    return shutil.which("claude") is not None and not os.environ.get("FORCE_MOCK_AGENT")


def run_agent_or_stub(
    role: str,
    skill_path: Optional[str],
    context: Dict[str, Any],
    app_working_dir: str,
    app_url: str,
    day: int,
) -> None:
    """Run one role's agent for this day.

    If a skill file path is configured AND the `claude` CLI is on PATH, call
    `claude --print` so the LLM agent makes the day's decisions. Otherwise fall
    back to the deterministic mock_agent.py.
    """
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / f"day-{day:03d}-{role}.log"
    context_json = json.dumps(context)

    if skill_path and _claude_available():
        skill_abs = str((PROJECT_ROOT / skill_path).resolve())
        prompt = (
            f"Read the skill file at {skill_abs}.\n"
            f"Today's context (market signal as JSON): {context_json}\n"
            "Execute your daily decisions following the skill's decision framework.\n"
            "Do NOT advance the day — the turn engine does that."
        )
        cmd = ["claude", "--print", "--prompt", prompt]
        mode = "claude"
    else:
        mock_path = str(PROJECT_ROOT / "mock_agent.py")
        cmd = [sys.executable, mock_path, role, app_url, context_json]
        mode = "mock"

    logger.info("[%s] running agent (%s) cwd=%s", role, mode, app_working_dir)
    try:
        result = subprocess.run(
            cmd,
            cwd=app_working_dir,
            capture_output=True,
            text=True,
            timeout=AGENT_TIMEOUT_S,
        )
        log_path.write_text(result.stdout + ("\n[stderr]\n" + result.stderr if result.stderr else ""))
        if result.returncode != 0:
            logger.warning("[%s] agent exited %s", role, result.returncode)
    except subprocess.TimeoutExpired:
        logger.error("[%s] agent timed out after %ss", role, AGENT_TIMEOUT_S)
        log_path.write_text(f"[timeout after {AGENT_TIMEOUT_S}s]\n")
    except Exception as exc:
        logger.error("[%s] agent failed: %s", role, exc)
        log_path.write_text(f"[error] {exc}\n")


ADVANCE_ENDPOINTS = {
    "retailer": "/api/v1/day/advance",
    "manufacturer": "/api/v1/simulate/advance",
    "provider": "/api/v1/day/advance",
}


def broadcast_signal(config: Dict[str, Any], signal: Dict[str, Any]) -> None:
    """POST today's signal to every app's `/api/v1/signal` endpoint.

    Done BEFORE agents run so a chip-shortage's `lead_time_modifier` is in
    effect when the manufacturer agent places orders with the provider.
    Apps that don't act on a given modifier still store it for observability.
    """
    base_payload: Dict[str, Any] = {
        "sim_day": signal["day"],
        "demand_modifier": signal.get("demand_modifier", 1.0),
        "supply_modifier": signal.get("supply_modifier", 1.0),
        "lead_time_modifier": signal.get("lead_time_modifier", 1.0),
    }
    retailer_payload = dict(base_payload)
    if "price_sensitivity" in signal:
        retailer_payload["price_sensitivity"] = signal["price_sensitivity"]

    targets: List[tuple[str, Dict[str, Any]]] = []
    for r in config.get("retailers", []):
        targets.append((r["url"], retailer_payload))
    manuf = config.get("manufacturer")
    if manuf:
        targets.append((manuf["url"], base_payload))
    for p in config.get("providers", []):
        targets.append((p["url"], base_payload))

    for url, payload in targets:
        try:
            resp = httpx.post(f"{url}/api/v1/signal", json=payload, timeout=10.0)
            if resp.status_code >= 400:
                logger.warning("signal POST %s failed: %s %s", url, resp.status_code, resp.text)
        except Exception as exc:
            logger.warning("signal POST %s failed: %s", url, exc)


def advance_all(config: Dict[str, Any]) -> None:
    """Advance every app's simulated day in retailer → manufacturer → provider order."""
    targets: List[tuple[str, str]] = []
    for r in config.get("retailers", []):
        targets.append((r["url"], ADVANCE_ENDPOINTS["retailer"]))
    manuf = config.get("manufacturer")
    if manuf:
        targets.append((manuf["url"], ADVANCE_ENDPOINTS["manufacturer"]))
    for p in config.get("providers", []):
        targets.append((p["url"], ADVANCE_ENDPOINTS["provider"]))

    for url, endpoint in targets:
        try:
            resp = httpx.post(f"{url}{endpoint}", timeout=15.0)
            if resp.status_code >= 400:
                logger.error("advance %s failed: %s %s", url, resp.status_code, resp.text)
        except Exception as exc:
            logger.warning("advance %s failed: %s", url, exc)


def log_day_summary(config: Dict[str, Any], day: int) -> None:
    """Print the one-line per-day summary the PDF requires.

    Aggregates outcomes across every configured retailer.
    """
    placed = fulfilled = backordered = stockouts = 0
    for retailer in config.get("retailers", []):
        url = retailer["url"].rstrip("/")
        try:
            resp = httpx.get(f"{url}/api/v1/day/summary?day={day}", timeout=10.0)
            if resp.status_code >= 400:
                logger.warning("summary fetch %s failed: %s", url, resp.status_code)
                continue
            data = resp.json()
            placed += data.get("placed", 0)
            fulfilled += data.get("fulfilled", 0)
            backordered += data.get("backordered", 0)
            stockouts += data.get("stockouts", 0)
        except Exception as exc:
            logger.warning("summary fetch %s failed: %s", url, exc)

    logger.info(
        "Day %s: %s placed / %s fulfilled / %s backordered / %s stockouts",
        day,
        placed,
        fulfilled,
        backordered,
        stockouts,
    )


def run_day(day: int, config: Dict[str, Any], scenario: Dict[str, Any]) -> None:
    signal = todays_signal(day, scenario)
    logger.info("=" * 60)
    logger.info(" DAY %s  modifier=%s supply=%s events=%s",
                day,
                signal["demand_modifier"],
                signal["supply_modifier"],
                [e.get("name") for e in signal["events"]] or "none")
    logger.info("=" * 60)

    # Push today's signal to every app BEFORE agents act, so e.g. a chip-shortage
    # lead_time_modifier is in effect when the manufacturer places orders.
    broadcast_signal(config, signal)

    for retailer in config.get("retailers", []):
        n = generate_customer_orders(retailer, signal)
        logger.info("retailer %s: injected %s customer orders", retailer["name"], n)

    for retailer in config.get("retailers", []):
        run_agent_or_stub(
            role=f"retailer-{retailer['name']}",
            skill_path=retailer.get("skill"),
            context=signal,
            app_working_dir=str((PROJECT_ROOT / retailer["path"]).resolve()),
            app_url=retailer["url"],
            day=day,
        )

    manuf = config["manufacturer"]
    run_agent_or_stub(
        role="manufacturer",
        skill_path=manuf.get("skill"),
        context=signal,
        app_working_dir=str((PROJECT_ROOT / manuf["path"]).resolve()),
        app_url=manuf["url"],
        day=day,
    )

    for provider in config.get("providers", []):
        run_agent_or_stub(
            role=f"provider-{provider['name']}",
            skill_path=provider.get("skill"),
            context=signal,
            app_working_dir=str((PROJECT_ROOT / provider["path"]).resolve()),
            app_url=provider["url"],
            day=day,
        )

    advance_all(config)
    log_day_summary(config, day)


def archive_dbs(run_tag: str) -> Path:
    """Copy each app's live SQLite file into `runs/<run_tag>/`.

    Used after a run completes so `analyze_sim.py --db-dir runs/<tag>` and
    `compare_scenarios.py` can read it without colliding with the next run.
    """
    dest = RUNS_DIR / run_tag
    dest.mkdir(parents=True, exist_ok=True)
    for name, src in APP_DB_FILES.items():
        if not src.exists():
            logger.warning("archive: %s DB missing at %s", name, src)
            continue
        shutil.copy2(src, dest / src.name)
    logger.info("archived run DBs to %s", dest)
    return dest


def _pop_arg(args: List[str], name: str) -> Optional[str]:
    if name in args:
        idx = args.index(name)
        if idx + 1 >= len(args):
            raise SystemExit(f"{name} requires a value")
        value = args[idx + 1]
        del args[idx:idx + 2]
        return value
    return None


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 3:
        print(
            "Usage: python turn_engine.py <config.json> <scenario.json> <num_days> "
            "[--seed N] [--run-tag NAME]"
        )
        sys.exit(1)

    seed = _pop_arg(args, "--seed")
    run_tag = _pop_arg(args, "--run-tag")

    if len(args) < 3:
        print("missing positional arguments after option parsing", file=sys.stderr)
        sys.exit(1)

    config_path, scenario_path, num_days = args[0], args[1], int(args[2])
    if seed is not None:
        random.seed(int(seed))

    config = load_config(config_path)
    scenario = load_scenario(scenario_path)

    LOGS_DIR.mkdir(exist_ok=True)
    for day in range(1, num_days + 1):
        run_day(day, config, scenario)

    if run_tag:
        archive_dbs(run_tag)


if __name__ == "__main__":
    main()
