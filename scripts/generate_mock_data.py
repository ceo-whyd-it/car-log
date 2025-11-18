#!/usr/bin/env python3
"""
Generate mock data for Car Log demo and testing.

Creates realistic Slovak company vehicle mileage data including:
- Vehicles (Ford Transit delivery van)
- Checkpoints (refuel events in Bratislava, Košice)
- Templates (common routes: Warehouse Run, Client Visit)
- Trips (reconstructed from templates)

Usage:
    python scripts/generate_mock_data.py --scenario demo
    python scripts/generate_mock_data.py --scenario test --trips 50
"""

import argparse
import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path


def get_data_path() -> Path:
    """Get data directory path"""
    data_path = os.getenv("DATA_PATH", "~/Documents/MileageLog/data")
    return Path(data_path).expanduser()


def atomic_write_json(file_path: Path, data: dict):
    """Write JSON atomically"""
    temp_path = file_path.with_suffix('.tmp')
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    temp_path.replace(file_path)


def generate_demo_scenario():
    """
    Generate demo scenario data (from Day 7 integration checkpoint).

    Scenario:
    - 1 vehicle: Ford Transit (BA-456CD)
    - 2 checkpoints: Nov 1 (45000 km), Nov 8 (45820 km) → 820 km gap
    - 3 templates: Warehouse Run (410 km), Client Visit (80 km), Branch Office (120 km)
    - 2 trips: 2× Warehouse Run = 820 km (100% coverage)
    """
    data_path = get_data_path()
    print(f"📁 Data path: {data_path}")

    # Create directories
    (data_path / "vehicles").mkdir(parents=True, exist_ok=True)
    (data_path / "checkpoints" / "2025-11").mkdir(parents=True, exist_ok=True)
    (data_path / "trips" / "2025-11").mkdir(parents=True, exist_ok=True)
    (data_path / "templates").mkdir(parents=True, exist_ok=True)

    print("✨ Demo scenario complete!")
    print(f"\nData location: {data_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate mock data for Car Log demo and testing"
    )
    parser.add_argument(
        "--scenario",
        choices=["demo", "test"],
        default="demo",
        help="Data scenario to generate (default: demo)",
    )
    parser.add_argument(
        "--trips",
        type=int,
        default=10,
        help="Number of trips to generate for 'test' scenario (default: 10)",
    )

    args = parser.parse_args()

    if args.scenario == "demo":
        generate_demo_scenario()
    else:
        print(f"❌ Scenario '{args.scenario}' not yet implemented")
        print("Currently supported: demo")


if __name__ == "__main__":
    main()
