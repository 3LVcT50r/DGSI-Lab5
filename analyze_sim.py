#!/usr/bin/env python3
"""Generate the four Week 8 analysis charts from each app's `metrics` table.

The Week 8 PDF asks for, per scenario run:
  1. Inventory over time — 3 lines (parts@mfg, printers@mfg, printers@retailer)
  2. Prices over time    — 3 lines (provider top-tier, mfg wholesale, retail)
  3. Order fulfillment   — daily bars (placed vs fulfilled vs backordered)
  4. Events overlay      — vertical bands marking when each scenario event
                            was active, drawn ON TOP of the three charts above

Reads SQLite files directly so the apps do not have to be running. Run with:

    python analyze_sim.py scenarios/holiday-rush.json --out reports/holiday-rush

The `--out` directory is created if missing.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import matplotlib

matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
DEFAULT_PROVIDER_DB = ROOT / "provider-app" / "data" / "provider.sqlite"
DEFAULT_FACTORY_DB = ROOT / "factory-app" / "data" / "database.sqlite"
DEFAULT_RETAILER_DB = ROOT / "retailer-app" / "data" / "retailer.sqlite"


def resolve_db_paths(db_dir: Optional[Path]) -> Dict[str, Path]:
    """Resolve provider/factory/retailer DB locations.

    If `db_dir` is given (used for archived runs), look inside it; otherwise
    use the live in-place app DBs. The expected filenames inside `db_dir`
    are the same the apps write: provider.sqlite, database.sqlite,
    retailer.sqlite.
    """
    if db_dir is None:
        return {
            "provider": DEFAULT_PROVIDER_DB,
            "factory": DEFAULT_FACTORY_DB,
            "retailer": DEFAULT_RETAILER_DB,
        }
    return {
        "provider": db_dir / "provider.sqlite",
        "factory": db_dir / "database.sqlite",
        "retailer": db_dir / "retailer.sqlite",
    }

EVENT_COLOURS = ["#ffd166", "#ef476f", "#06d6a0", "#118ab2", "#9b5de5", "#f15bb5"]


@dataclass
class ScenarioEvent:
    name: str
    start_day: int
    end_day: int
    description: str = ""


def load_scenario_events(scenario_path: Path) -> List[ScenarioEvent]:
    payload = json.loads(scenario_path.read_text(encoding="utf-8"))
    events: List[ScenarioEvent] = []
    for raw in payload.get("events", []):
        events.append(
            ScenarioEvent(
                name=raw.get("name", "event"),
                start_day=int(raw.get("start_day", 1)),
                end_day=int(raw.get("end_day", 1)),
                description=raw.get("description", ""),
            )
        )
    return events


def _read_table(db_path: Path, table: str) -> pd.DataFrame:
    """Read `table` from `db_path` into a DataFrame, returning empty if missing.

    Returning empty (rather than raising) keeps the analyzer useful when one
    of the apps had nothing to snapshot — the chart for the others still
    renders.
    """
    if not db_path.exists():
        print(f"[warn] missing DB: {db_path}", file=sys.stderr)
        return pd.DataFrame()
    with sqlite3.connect(str(db_path)) as conn:
        try:
            return pd.read_sql_query(f"SELECT * FROM {table}", conn)
        except pd.io.sql.DatabaseError as exc:
            print(f"[warn] {db_path}::{table} unreadable: {exc}", file=sys.stderr)
            return pd.DataFrame()


def _overlay_events(ax: plt.Axes, events: Sequence[ScenarioEvent]) -> None:
    """Shade each scenario event as a vertical band on `ax`."""
    for idx, event in enumerate(events):
        colour = EVENT_COLOURS[idx % len(EVENT_COLOURS)]
        ax.axvspan(
            event.start_day - 0.5,
            event.end_day + 0.5,
            alpha=0.15,
            color=colour,
            label=event.name if idx == 0 or True else None,
        )
        # Place the event name at the top of the band
        ymin, ymax = ax.get_ylim()
        ax.text(
            (event.start_day + event.end_day) / 2.0,
            ymax * 0.97 if ymax > 0 else 0,
            event.name,
            ha="center",
            va="top",
            fontsize=8,
            color="#333333",
            alpha=0.75,
            rotation=0,
        )


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    print(f"wrote {path}")


def chart_inventory_over_time(
    factory: pd.DataFrame,
    retailer: pd.DataFrame,
    events: Sequence[ScenarioEvent],
    out_path: Path,
) -> None:
    """Three-line inventory chart: parts@mfg, printers@mfg, printers@retailer."""
    fig, ax = plt.subplots(figsize=(10, 5.5))

    if not factory.empty:
        parts = (
            factory[factory["product_type"] == "raw"]
            .groupby("sim_day")["stock_qty"].sum().reset_index()
        )
        printers_mfg = (
            factory[factory["product_type"] == "finished"]
            .groupby("sim_day")["stock_qty"].sum().reset_index()
        )
        if not parts.empty:
            ax.plot(parts["sim_day"], parts["stock_qty"], label="Parts @ Manufacturer", color="#118ab2", lw=2)
        if not printers_mfg.empty:
            ax.plot(printers_mfg["sim_day"], printers_mfg["stock_qty"], label="Finished printers @ Manufacturer", color="#073b4c", lw=2)

    if not retailer.empty:
        printers_ret = retailer.groupby("sim_day")["printer_stock"].sum().reset_index()
        ax.plot(printers_ret["sim_day"], printers_ret["printer_stock"], label="Printers @ Retailer", color="#ef476f", lw=2)

    ax.set_title("Inventory over time")
    ax.set_xlabel("Simulation day")
    ax.set_ylabel("Units in stock")
    ax.grid(True, alpha=0.3)
    _overlay_events(ax, events)
    ax.legend(loc="upper right")
    _save(fig, out_path)


def chart_prices_over_time(
    provider: pd.DataFrame,
    factory: pd.DataFrame,
    retailer: pd.DataFrame,
    events: Sequence[ScenarioEvent],
    out_path: Path,
) -> None:
    """Three-line price chart: provider top-tier, mfg wholesale, retailer retail.

    Picks the first product seen in each app's metrics as the representative
    line. If you want a specific product, filter the DataFrames before
    calling.
    """
    fig, ax = plt.subplots(figsize=(10, 5.5))

    def _pick_first(df: pd.DataFrame, value_col: str) -> Optional[pd.DataFrame]:
        if df.empty or value_col not in df.columns:
            return None
        product_name = df["product_name"].dropna().iloc[0] if not df["product_name"].dropna().empty else None
        if product_name is None:
            return None
        sub = df[df["product_name"] == product_name][["sim_day", value_col]].dropna()
        return sub.sort_values("sim_day"), product_name

    pf = _pick_first(provider, "top_tier_price") if not provider.empty else None
    if pf is not None:
        sub, name = pf
        ax.plot(sub["sim_day"], sub["top_tier_price"], label=f"Provider top-tier ({name})", color="#118ab2", lw=2)

    if not factory.empty:
        finished = factory[(factory["product_type"] == "finished") & factory["wholesale_price"].notna()]
        if not finished.empty:
            name = finished["product_name"].iloc[0]
            sub = finished[finished["product_name"] == name][["sim_day", "wholesale_price"]].sort_values("sim_day")
            ax.plot(sub["sim_day"], sub["wholesale_price"], label=f"Manufacturer wholesale ({name})", color="#073b4c", lw=2)

    rf = _pick_first(retailer, "retail_price") if not retailer.empty else None
    if rf is not None:
        sub, name = rf
        ax.plot(sub["sim_day"], sub["retail_price"], label=f"Retailer retail ({name})", color="#ef476f", lw=2)

    ax.set_title("Prices over time")
    ax.set_xlabel("Simulation day")
    ax.set_ylabel("Price (EUR)")
    ax.grid(True, alpha=0.3)
    _overlay_events(ax, events)
    ax.legend(loc="upper right")
    _save(fig, out_path)


def chart_order_fulfillment(
    retailer: pd.DataFrame,
    events: Sequence[ScenarioEvent],
    out_path: Path,
) -> None:
    """Stacked bars per day: placed vs fulfilled vs backordered."""
    fig, ax = plt.subplots(figsize=(10, 5.5))

    if retailer.empty:
        ax.text(0.5, 0.5, "no retailer metrics", ha="center", va="center", transform=ax.transAxes)
    else:
        agg = (
            retailer.groupby("sim_day")[
                ["orders_placed_today", "orders_fulfilled_today", "orders_backordered_today"]
            ]
            .sum()
            .reset_index()
        )
        width = 0.27
        days = agg["sim_day"]
        ax.bar(days - width, agg["orders_placed_today"], width=width, label="Placed", color="#118ab2")
        ax.bar(days, agg["orders_fulfilled_today"], width=width, label="Fulfilled", color="#06d6a0")
        ax.bar(days + width, agg["orders_backordered_today"], width=width, label="Backordered", color="#ef476f")

    ax.set_title("Daily customer order outcomes")
    ax.set_xlabel("Simulation day")
    ax.set_ylabel("Orders")
    ax.grid(True, axis="y", alpha=0.3)
    _overlay_events(ax, events)
    ax.legend(loc="upper right")
    _save(fig, out_path)


def chart_events_strip(events: Sequence[ScenarioEvent], total_days: int, out_path: Path) -> None:
    """Standalone strip chart showing event bands, useful in slides."""
    fig, ax = plt.subplots(figsize=(10, 2.5))
    ax.set_xlim(0.5, max(total_days, 1) + 0.5)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    for idx, event in enumerate(events):
        colour = EVENT_COLOURS[idx % len(EVENT_COLOURS)]
        ax.axvspan(event.start_day - 0.5, event.end_day + 0.5, color=colour, alpha=0.35, label=event.name)
        ax.text(
            (event.start_day + event.end_day) / 2.0,
            0.5,
            event.name,
            ha="center",
            va="center",
            fontsize=9,
            color="#222222",
        )
    ax.set_xlabel("Simulation day")
    ax.set_title("Scenario events")
    _save(fig, out_path)


def _resolve_out_dir(arg: Optional[str], scenario_path: Path) -> Path:
    if arg:
        return Path(arg)
    return ROOT / "reports" / scenario_path.stem


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Week 8 simulation charts from each app's metrics table.")
    parser.add_argument("scenario", help="Scenario JSON used for the run (read for event overlay).")
    parser.add_argument("--out", help="Output directory for PNGs. Default: reports/<scenario-stem>/")
    parser.add_argument(
        "--db-dir",
        help="Directory containing archived provider.sqlite / database.sqlite / retailer.sqlite. Defaults to the live app DBs.",
    )
    parser.add_argument(
        "--total-days",
        type=int,
        default=None,
        help="Total simulation days (used for the events strip chart). Defaults to max event end_day.",
    )
    args = parser.parse_args()

    scenario_path = Path(args.scenario).resolve()
    if not scenario_path.exists():
        parser.error(f"scenario file not found: {scenario_path}")

    events = load_scenario_events(scenario_path)
    out_dir = _resolve_out_dir(args.out, scenario_path)

    db_paths = resolve_db_paths(Path(args.db_dir).resolve() if args.db_dir else None)
    provider_metrics = _read_table(db_paths["provider"], "metrics")
    factory_metrics = _read_table(db_paths["factory"], "metrics")
    retailer_metrics = _read_table(db_paths["retailer"], "metrics")

    if provider_metrics.empty and factory_metrics.empty and retailer_metrics.empty:
        print("[error] no metrics found in any DB — run a simulation first.", file=sys.stderr)
        sys.exit(2)

    chart_inventory_over_time(factory_metrics, retailer_metrics, events, out_dir / "inventory_over_time.png")
    chart_prices_over_time(provider_metrics, factory_metrics, retailer_metrics, events, out_dir / "prices_over_time.png")
    chart_order_fulfillment(retailer_metrics, events, out_dir / "order_fulfillment.png")

    total_days = args.total_days or (max((e.end_day for e in events), default=0))
    chart_events_strip(events, total_days, out_dir / "events_strip.png")


if __name__ == "__main__":
    main()
