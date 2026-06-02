#!/usr/bin/env python3
"""Side-by-side charts comparing two archived simulation runs.

Typical workflow:

    python turn_engine.py config/sim.json scenarios/calm-market.json 25 --run-tag calm
    # reset DBs (rm runs are independent; archive is the snapshot you keep)
    python turn_engine.py config/sim.json scenarios/holiday-rush.json 25 --run-tag holiday
    python compare_scenarios.py \\
        --run-a runs/calm     --scenario-a scenarios/calm-market.json   --label-a "Calm" \\
        --run-b runs/holiday  --scenario-b scenarios/holiday-rush.json  --label-b "Holiday" \\
        --out reports/calm-vs-holiday

Produces three two-panel PNGs (inventory, prices, fulfillment) with the
scenario-event bands of each run drawn under its panel.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from analyze_sim import (
    EVENT_COLOURS,
    ScenarioEvent,
    _read_table,
    load_scenario_events,
    resolve_db_paths,
)

ROOT = Path(__file__).resolve().parent


def _overlay(ax: plt.Axes, events: Sequence[ScenarioEvent]) -> None:
    for idx, event in enumerate(events):
        ax.axvspan(
            event.start_day - 0.5,
            event.end_day + 0.5,
            alpha=0.13,
            color=EVENT_COLOURS[idx % len(EVENT_COLOURS)],
        )


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    print(f"wrote {path}")


def compare_inventory(
    factory_a: pd.DataFrame, retailer_a: pd.DataFrame, events_a, label_a: str,
    factory_b: pd.DataFrame, retailer_b: pd.DataFrame, events_b, label_b: str,
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), sharey=True)
    for ax, factory, retailer, events, label in (
        (axes[0], factory_a, retailer_a, events_a, label_a),
        (axes[1], factory_b, retailer_b, events_b, label_b),
    ):
        if not factory.empty:
            parts = factory[factory["product_type"] == "raw"].groupby("sim_day")["stock_qty"].sum().reset_index()
            printers = factory[factory["product_type"] == "finished"].groupby("sim_day")["stock_qty"].sum().reset_index()
            if not parts.empty:
                ax.plot(parts["sim_day"], parts["stock_qty"], label="Parts @ Manufacturer", color="#118ab2", lw=2)
            if not printers.empty:
                ax.plot(printers["sim_day"], printers["stock_qty"], label="Printers @ Manufacturer", color="#073b4c", lw=2)
        if not retailer.empty:
            ret = retailer.groupby("sim_day")["printer_stock"].sum().reset_index()
            ax.plot(ret["sim_day"], ret["printer_stock"], label="Printers @ Retailer", color="#ef476f", lw=2)
        ax.set_title(label)
        ax.set_xlabel("Simulation day")
        ax.grid(True, alpha=0.3)
        _overlay(ax, events)
        ax.legend(loc="upper right", fontsize=8)
    axes[0].set_ylabel("Units in stock")
    fig.suptitle("Inventory: calm vs volatile")
    _save(fig, out_path)


def compare_prices(
    provider_a, factory_a, retailer_a, events_a, label_a: str,
    provider_b, factory_b, retailer_b, events_b, label_b: str,
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), sharey=True)
    for ax, provider, factory, retailer, events, label in (
        (axes[0], provider_a, factory_a, retailer_a, events_a, label_a),
        (axes[1], provider_b, factory_b, retailer_b, events_b, label_b),
    ):
        if not provider.empty and provider["product_name"].dropna().size:
            name = provider["product_name"].dropna().iloc[0]
            sub = provider[provider["product_name"] == name][["sim_day", "top_tier_price"]].dropna().sort_values("sim_day")
            ax.plot(sub["sim_day"], sub["top_tier_price"], label=f"Provider ({name})", color="#118ab2", lw=2)
        if not factory.empty:
            finished = factory[(factory["product_type"] == "finished") & factory["wholesale_price"].notna()]
            if not finished.empty:
                name = finished["product_name"].iloc[0]
                sub = finished[finished["product_name"] == name][["sim_day", "wholesale_price"]].sort_values("sim_day")
                ax.plot(sub["sim_day"], sub["wholesale_price"], label=f"Wholesale ({name})", color="#073b4c", lw=2)
        if not retailer.empty and retailer["product_name"].dropna().size:
            name = retailer["product_name"].dropna().iloc[0]
            sub = retailer[retailer["product_name"] == name][["sim_day", "retail_price"]].dropna().sort_values("sim_day")
            ax.plot(sub["sim_day"], sub["retail_price"], label=f"Retail ({name})", color="#ef476f", lw=2)
        ax.set_title(label)
        ax.set_xlabel("Simulation day")
        ax.grid(True, alpha=0.3)
        _overlay(ax, events)
        ax.legend(loc="upper right", fontsize=8)
    axes[0].set_ylabel("Price (EUR)")
    fig.suptitle("Prices: calm vs volatile")
    _save(fig, out_path)


def compare_fulfillment(
    retailer_a: pd.DataFrame, events_a, label_a: str,
    retailer_b: pd.DataFrame, events_b, label_b: str,
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), sharey=True)
    for ax, retailer, events, label in (
        (axes[0], retailer_a, events_a, label_a),
        (axes[1], retailer_b, events_b, label_b),
    ):
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
        ax.set_title(label)
        ax.set_xlabel("Simulation day")
        ax.grid(True, axis="y", alpha=0.3)
        _overlay(ax, events)
        ax.legend(loc="upper right", fontsize=8)
    axes[0].set_ylabel("Customer orders")
    fig.suptitle("Order outcomes: calm vs volatile")
    _save(fig, out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two archived simulation runs side-by-side.")
    parser.add_argument("--run-a", required=True, help="Path to first archived runs/<tag>/ directory.")
    parser.add_argument("--run-b", required=True, help="Path to second archived runs/<tag>/ directory.")
    parser.add_argument("--scenario-a", required=True, help="Scenario JSON for run A (used for event overlay).")
    parser.add_argument("--scenario-b", required=True, help="Scenario JSON for run B (used for event overlay).")
    parser.add_argument("--label-a", default="A")
    parser.add_argument("--label-b", default="B")
    parser.add_argument("--out", default="reports/compare", help="Output directory for PNGs.")
    args = parser.parse_args()

    paths_a = resolve_db_paths(Path(args.run_a).resolve())
    paths_b = resolve_db_paths(Path(args.run_b).resolve())
    events_a = load_scenario_events(Path(args.scenario_a))
    events_b = load_scenario_events(Path(args.scenario_b))

    provider_a = _read_table(paths_a["provider"], "metrics")
    factory_a = _read_table(paths_a["factory"], "metrics")
    retailer_a = _read_table(paths_a["retailer"], "metrics")
    provider_b = _read_table(paths_b["provider"], "metrics")
    factory_b = _read_table(paths_b["factory"], "metrics")
    retailer_b = _read_table(paths_b["retailer"], "metrics")

    out_dir = Path(args.out)
    compare_inventory(factory_a, retailer_a, events_a, args.label_a,
                      factory_b, retailer_b, events_b, args.label_b,
                      out_dir / "inventory_compare.png")
    compare_prices(provider_a, factory_a, retailer_a, events_a, args.label_a,
                   provider_b, factory_b, retailer_b, events_b, args.label_b,
                   out_dir / "prices_compare.png")
    compare_fulfillment(retailer_a, events_a, args.label_a,
                        retailer_b, events_b, args.label_b,
                        out_dir / "fulfillment_compare.png")


if __name__ == "__main__":
    main()
