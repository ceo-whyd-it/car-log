#!/usr/bin/env python3
"""
Mock Data Generator for Car Log Demo

Generates realistic Slovak test data for hackathon demo:
- Vehicles with valid VINs and Slovak license plates
- Checkpoints with GPS coordinates (Bratislava, Košice, etc.)
- Templates for common Slovak routes
- Realistic fuel consumption data
- Gap scenarios for trip reconstruction testing

Usage:
    python scripts/generate_mock_data.py
    python scripts/generate_mock_data.py --output ./demo-data
    python scripts/generate_mock_data.py --vehicles 3 --checkpoints 20
"""

import json
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import argparse


# ============================================================================
# SLOVAK REFERENCE DATA
# ============================================================================

SLOVAK_CITIES = {
    "Bratislava": {"lat": 48.1486, "lng": 17.1077, "name": "Bratislava"},
    "Košice": {"lat": 48.7164, "lng": 21.2611, "name": "Košice"},
    "Prešov": {"lat": 49.0014, "lng": 21.2393, "name": "Prešov"},
    "Žilina": {"lat": 49.2231, "lng": 18.7397, "name": "Žilina"},
    "Banská Bystrica": {"lat": 48.7355, "lng": 19.1535, "name": "Banská Bystrica"},
    "Nitra": {"lat": 48.3069, "lng": 18.0872, "name": "Nitra"},
    "Trenčín": {"lat": 48.8955, "lng": 18.0446, "name": "Trenčín"},
    "Martin": {"lat": 49.0661, "lng": 18.9211, "name": "Martin"},
    "Trnava": {"lat": 48.3774, "lng": 17.5880, "name": "Trnava"},
    "Poprad": {"lat": 49.0614, "lng": 20.2983, "name": "Poprad"},
}

FUEL_STATIONS = [
    {"name": "Shell Bratislava West", "city": "Bratislava"},
    {"name": "OMV Košice East", "city": "Košice"},
    {"name": "MOL Žilina North", "city": "Žilina"},
    {"name": "Slovnaft Prešov", "city": "Prešov"},
    {"name": "Benzinol Nitra", "city": "Nitra"},
]

BUSINESS_ROUTES = [
    {
        "name": "Warehouse Run to Košice",
        "from": "Bratislava",
        "to": "Košice",
        "distance_km": 410,
        "description": "Weekly warehouse pickup",
        "typical_days": ["Monday", "Thursday"]
    },
    {
        "name": "Client Visit Žilina",
        "from": "Bratislava",
        "to": "Žilina",
        "distance_km": 200,
        "description": "Sales meeting with client",
        "typical_days": ["Tuesday", "Wednesday"]
    },
    {
        "name": "Branch Office Prešov",
        "from": "Košice",
        "to": "Prešov",
        "distance_km": 35,
        "description": "Regional office visit",
        "typical_days": ["Friday"]
    },
]

VEHICLE_TEMPLATES = [
    {
        "make": "Ford",
        "model": "Transit",
        "year": 2022,
        "fuel_type": "Diesel",
        "avg_efficiency": 8.5,  # L/100km
        "tank_capacity": 80
    },
    {
        "make": "Volkswagen",
        "model": "Transporter",
        "year": 2021,
        "fuel_type": "Diesel",
        "avg_efficiency": 7.8,
        "tank_capacity": 70
    },
    {
        "make": "Mercedes-Benz",
        "model": "Sprinter",
        "year": 2023,
        "fuel_type": "Diesel",
        "avg_efficiency": 9.2,
        "tank_capacity": 90
    },
]


# ============================================================================
# VIN GENERATION (Slovak Tax Compliant)
# ============================================================================

def generate_valid_vin() -> str:
    """
    Generate valid 17-character VIN (no I, O, Q characters)
    Format: WMI (3) + VDS (6) + VIS (8) = 17 characters
    """
    # WMI: World Manufacturer Identifier (3 chars)
    wmi_codes = ["WBA", "WDB", "WVW", "TMB", "VF1", "SCC"]  # BMW, Mercedes, VW, Skoda, Renault, Lotus
    wmi = random.choice(wmi_codes)

    # VDS: Vehicle Descriptor Section (6 chars)
    # VIS: Vehicle Identifier Section (8 chars)
    valid_chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"  # No I, O, Q

    vds_vis = ''.join(random.choices(valid_chars, k=14))

    return f"{wmi}{vds_vis}"


def generate_slovak_license_plate() -> str:
    """
    Generate Slovak license plate: XX-###XX
    Examples: BA-456CD, KE-123AB, ZA-789EF
    """
    # Slovak region codes
    regions = ["BA", "KE", "ZA", "TT", "NR", "TN", "BB", "PO", "PE", "MT"]
    region = random.choice(regions)

    numbers = f"{random.randint(100, 999)}"
    letters = ''.join(random.choices("ABCDEFGHKLMNPRSTUVWXYZ", k=2))  # No I, O, Q, J

    return f"{region}-{numbers}{letters}"


# ============================================================================
# DATA GENERATORS
# ============================================================================

def generate_vehicle(vehicle_id: str, template: Dict) -> Dict[str, Any]:
    """Generate a vehicle with Slovak compliance fields"""
    now = datetime.now().isoformat() + "Z"

    return {
        "vehicle_id": vehicle_id,
        "name": f"{template['make']} {template['model']} Delivery Van",
        "license_plate": generate_slovak_license_plate(),
        "vin": generate_valid_vin(),
        "make": template["make"],
        "model": template["model"],
        "year": template["year"],
        "fuel_type": template["fuel_type"],
        "initial_odometer_km": random.randint(10000, 50000),
        "current_odometer_km": random.randint(50000, 100000),
        "average_efficiency_l_per_100km": template["avg_efficiency"],
        "tank_capacity_liters": template["tank_capacity"],
        "active": True,
        "created_at": now,
        "updated_at": now
    }


def generate_checkpoint(
    checkpoint_id: str,
    vehicle: Dict,
    datetime_str: str,
    odometer_km: int,
    city: str,
    fuel_station: Dict,
    checkpoint_type: str = "refuel"
) -> Dict[str, Any]:
    """Generate a checkpoint with GPS coordinates and optional receipt"""
    city_data = SLOVAK_CITIES[city]

    # Add small random offset to GPS (simulate different locations in city)
    lat = city_data["lat"] + random.uniform(-0.02, 0.02)
    lng = city_data["lng"] + random.uniform(-0.02, 0.02)

    checkpoint = {
        "checkpoint_id": checkpoint_id,
        "vehicle_id": vehicle["vehicle_id"],
        "checkpoint_type": checkpoint_type,
        "datetime": datetime_str,
        "odometer_km": odometer_km,
        "location": {
            "coords": {
                "latitude": round(lat, 6),
                "longitude": round(lng, 6)
            },
            "address": f"{fuel_station['name']}, {city}, Slovakia",
            "source": "exif"
        },
        "photos": [f"photos/dashboard_{checkpoint_id}.jpg"],
        "created_at": datetime_str,
        "updated_at": datetime_str
    }

    # Add receipt data if refuel checkpoint
    if checkpoint_type == "refuel":
        fuel_liters = random.randint(40, 70)
        price_per_liter = round(random.uniform(1.35, 1.55), 2)
        price_incl_vat = round(fuel_liters * price_per_liter, 2)
        vat_rate = 0.20  # Slovak VAT rate
        price_excl_vat = round(price_incl_vat / (1 + vat_rate), 2)

        checkpoint["receipt"] = {
            "receipt_id": f"SK-{random.randint(100000, 999999)}",
            "vendor_name": fuel_station["name"],
            "datetime": datetime_str,
            "fuel_type": vehicle["fuel_type"],
            "fuel_liters": fuel_liters,
            "price_per_liter_eur": price_per_liter,
            "price_excl_vat_eur": price_excl_vat,
            "price_incl_vat_eur": price_incl_vat,
            "vat_amount_eur": round(price_incl_vat - price_excl_vat, 2),
            "vat_rate": vat_rate,
            "payment_method": "card"
        }

    return checkpoint


def generate_template(template_id: str, route: Dict) -> Dict[str, Any]:
    """Generate a trip template for business route"""
    from_city = SLOVAK_CITIES[route["from"]]
    to_city = SLOVAK_CITIES[route["to"]]

    now = datetime.now().isoformat() + "Z"

    return {
        "template_id": template_id,
        "name": route["name"],
        "from_coords": {
            "lat": from_city["lat"],
            "lng": from_city["lng"]
        },
        "from_address": f"{from_city['name']}, Slovakia",
        "from_label": from_city["name"],
        "to_coords": {
            "lat": to_city["lat"],
            "lng": to_city["lng"]
        },
        "to_address": f"{to_city['name']}, Slovakia",
        "to_label": to_city["name"],
        "distance_km": route["distance_km"],
        "is_round_trip": True,
        "typical_days": route["typical_days"],
        "purpose": "business",
        "business_description": route["description"],
        "usage_count": random.randint(5, 50),
        "last_used_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat() + "Z",
        "created_at": now,
        "updated_at": now
    }


def generate_trip(
    trip_id: str,
    vehicle: Dict,
    start_checkpoint: Dict,
    end_checkpoint: Dict,
    template: Dict,
    driver_name: str = "Ján Novák"
) -> Dict[str, Any]:
    """Generate a trip with Slovak compliance fields"""

    # Calculate trip metrics
    distance_km = template["distance_km"]
    fuel_efficiency = vehicle["average_efficiency_l_per_100km"] * random.uniform(0.9, 1.1)
    fuel_consumption_liters = round((distance_km / 100) * fuel_efficiency, 2)

    # Calculate cost from receipt data
    fuel_cost_eur = 0
    if "receipt" in end_checkpoint:
        fuel_cost_eur = end_checkpoint["receipt"]["price_incl_vat_eur"]

    # Trip timing (separate from refuel timing - Slovak requirement)
    start_dt = datetime.fromisoformat(start_checkpoint["datetime"].replace("Z", ""))
    trip_duration_hours = distance_km / 80  # Assume 80 km/h average
    end_dt = start_dt + timedelta(hours=trip_duration_hours)

    return {
        "trip_id": trip_id,
        "vehicle_id": vehicle["vehicle_id"],
        "start_checkpoint_id": start_checkpoint["checkpoint_id"],
        "end_checkpoint_id": end_checkpoint["checkpoint_id"],
        "template_id": template["template_id"],

        # Slovak compliance: Separate trip timing from refuel timing
        "trip_start_datetime": start_dt.isoformat() + "Z",
        "trip_end_datetime": end_dt.isoformat() + "Z",

        # Slovak compliance: Separate trip locations from fuel station
        "trip_start_location": template["from_address"],
        "trip_end_location": template["to_address"],
        "trip_start_coords": template["from_coords"],
        "trip_end_coords": template["to_coords"],

        # Slovak compliance: Driver information (MANDATORY)
        "driver_name": driver_name,
        "driver_is_owner": True,

        # Trip metrics
        "distance_km": distance_km,
        "fuel_consumption_liters": fuel_consumption_liters,
        "fuel_efficiency_l_per_100km": round(fuel_efficiency, 2),
        "fuel_cost_eur": fuel_cost_eur,

        # Purpose classification
        "purpose": "Business",
        "business_description": template["business_description"],

        # Refuel metadata
        "refuel_datetime": end_checkpoint["datetime"],
        "refuel_timing": "after",

        # Reconstruction metadata
        "reconstruction_method": "template",
        "template_used": template["name"],
        "confidence_score": round(random.uniform(0.85, 0.98), 2),

        "created_at": end_checkpoint["datetime"],
        "updated_at": end_checkpoint["datetime"]
    }


# ============================================================================
# ATOMIC WRITE PATTERN (CRITICAL - Prevents file corruption)
# ============================================================================

def atomic_write_json(file_path: Path, data: Dict[str, Any]) -> None:
    """
    Write JSON file atomically (crash-safe)

    Uses temp file + rename pattern to ensure file is never corrupted
    even if process crashes during write.
    """
    import tempfile

    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file first
    fd, temp_path = tempfile.mkstemp(
        dir=file_path.parent,
        suffix='.tmp',
        text=True
    )

    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Atomic rename (POSIX guarantees atomicity)
        os.replace(temp_path, file_path)

    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise RuntimeError(f"Failed to write {file_path}: {e}")


# ============================================================================
# DEMO SCENARIO GENERATOR
# ============================================================================

def generate_demo_scenario(output_dir: Path) -> None:
    """
    Generate realistic demo scenario with gap detection opportunity

    Scenario:
    1. Vehicle registered on Nov 1
    2. First refuel checkpoint on Nov 1 (Bratislava, odometer: 45,000 km)
    3. Second refuel checkpoint on Nov 8 (Bratislava, odometer: 45,820 km)
    4. Gap detected: 820 km over 7 days
    5. Templates available: Warehouse Run to Košice (410 km round trip)
    6. Expected reconstruction: 2x Warehouse Run = 820 km (100% coverage)
    """

    print("\n🚀 Generating Demo Scenario...")

    # Create vehicle
    vehicle_template = VEHICLE_TEMPLATES[0]  # Ford Transit
    vehicle_id = str(uuid.uuid4())
    vehicle = generate_vehicle(vehicle_id, vehicle_template)

    # Create templates
    templates = []
    for route in BUSINESS_ROUTES:
        template_id = str(uuid.uuid4())
        template = generate_template(template_id, route)
        templates.append(template)

    # Create first checkpoint (Nov 1, 2025, 08:00)
    cp1_id = str(uuid.uuid4())
    cp1_datetime = "2025-11-01T08:00:00Z"
    cp1_odometer = 45000
    cp1 = generate_checkpoint(
        cp1_id,
        vehicle,
        cp1_datetime,
        cp1_odometer,
        "Bratislava",
        FUEL_STATIONS[0],
        "refuel"
    )

    # Create second checkpoint (Nov 8, 2025, 17:00)
    cp2_id = str(uuid.uuid4())
    cp2_datetime = "2025-11-08T17:00:00Z"
    cp2_odometer = 45820  # 820 km gap (2x Warehouse Run)
    cp2 = generate_checkpoint(
        cp2_id,
        vehicle,
        cp2_datetime,
        cp2_odometer,
        "Bratislava",
        FUEL_STATIONS[0],
        "refuel"
    )

    # Write files
    base_path = output_dir / "data"

    # Vehicle
    vehicle_file = base_path / "vehicles" / f"{vehicle_id}.json"
    atomic_write_json(vehicle_file, vehicle)
    print(f"✅ Vehicle: {vehicle_file}")

    # Templates
    for template in templates:
        template_file = base_path / "templates" / f"{template['template_id']}.json"
        atomic_write_json(template_file, template)
        print(f"✅ Template: {template['name']}")

    # Checkpoints
    cp1_file = base_path / "checkpoints" / "2025-11" / f"{cp1_id}.json"
    atomic_write_json(cp1_file, cp1)
    print(f"✅ Checkpoint 1: {cp1_datetime}, {cp1_odometer} km")

    cp2_file = base_path / "checkpoints" / "2025-11" / f"{cp2_id}.json"
    atomic_write_json(cp2_file, cp2)
    print(f"✅ Checkpoint 2: {cp2_datetime}, {cp2_odometer} km")

    # Summary
    gap_km = cp2_odometer - cp1_odometer
    print(f"\n📊 Demo Scenario Summary:")
    print(f"   Vehicle: {vehicle['name']} ({vehicle['license_plate']})")
    print(f"   VIN: {vehicle['vin']}")
    print(f"   Gap: {gap_km} km over 7 days")
    print(f"   Templates: {len(templates)} available")
    print(f"   Expected: 2x Warehouse Run to Košice (410 km × 2 = 820 km)")
    print(f"   Coverage: 100%")
    print(f"\n💡 Next steps:")
    print(f"   1. Start MCP servers")
    print(f"   2. Open Claude Desktop")
    print(f"   3. Say: 'Detect gap between checkpoints and reconstruct trips'")


def generate_full_dataset(
    output_dir: Path,
    num_vehicles: int = 3,
    num_checkpoints_per_vehicle: int = 10
) -> None:
    """Generate full dataset for comprehensive testing"""

    print(f"\n🚀 Generating Full Dataset...")
    print(f"   Vehicles: {num_vehicles}")
    print(f"   Checkpoints per vehicle: {num_checkpoints_per_vehicle}")

    base_path = output_dir / "data"

    # Generate vehicles
    vehicles = []
    for i, template in enumerate(VEHICLE_TEMPLATES[:num_vehicles]):
        vehicle_id = str(uuid.uuid4())
        vehicle = generate_vehicle(vehicle_id, template)
        vehicles.append(vehicle)

        vehicle_file = base_path / "vehicles" / f"{vehicle_id}.json"
        atomic_write_json(vehicle_file, vehicle)
        print(f"✅ Vehicle {i+1}: {vehicle['name']} ({vehicle['license_plate']})")

    # Generate templates (same for all vehicles)
    templates = []
    for route in BUSINESS_ROUTES:
        template_id = str(uuid.uuid4())
        template = generate_template(template_id, route)
        templates.append(template)

        template_file = base_path / "templates" / f"{template_id}.json"
        atomic_write_json(template_file, template)

    print(f"✅ Templates: {len(templates)} routes")

    # Generate checkpoints for each vehicle
    for vehicle in vehicles:
        odometer = vehicle["initial_odometer_km"]
        start_date = datetime(2025, 11, 1, 8, 0, 0)

        for j in range(num_checkpoints_per_vehicle):
            # Random interval between checkpoints (3-7 days)
            days_gap = random.randint(3, 7)
            checkpoint_datetime = start_date + timedelta(days=days_gap * j)

            # Random odometer increase (200-600 km)
            odometer += random.randint(200, 600)

            # Random city and fuel station
            city = random.choice(list(SLOVAK_CITIES.keys()))
            fuel_station = random.choice([fs for fs in FUEL_STATIONS if fs["city"] == city] or FUEL_STATIONS)

            checkpoint_id = str(uuid.uuid4())
            checkpoint = generate_checkpoint(
                checkpoint_id,
                vehicle,
                checkpoint_datetime.isoformat() + "Z",
                odometer,
                city,
                fuel_station,
                "refuel"
            )

            month_str = checkpoint_datetime.strftime("%Y-%m")
            checkpoint_file = base_path / "checkpoints" / month_str / f"{checkpoint_id}.json"
            atomic_write_json(checkpoint_file, checkpoint)

    print(f"✅ Checkpoints: {num_vehicles * num_checkpoints_per_vehicle} total")
    print(f"\n✨ Full dataset generated at: {base_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate mock data for Car Log demo"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./demo-data",
        help="Output directory (default: ./demo-data)"
    )
    parser.add_argument(
        "--scenario",
        choices=["demo", "full"],
        default="demo",
        help="Generate demo scenario or full dataset (default: demo)"
    )
    parser.add_argument(
        "--vehicles",
        type=int,
        default=3,
        help="Number of vehicles (full dataset only, default: 3)"
    )
    parser.add_argument(
        "--checkpoints",
        type=int,
        default=10,
        help="Checkpoints per vehicle (full dataset only, default: 10)"
    )

    args = parser.parse_args()

    output_dir = Path(args.output)

    print("=" * 60)
    print("🚗 Car Log Mock Data Generator")
    print("=" * 60)

    if args.scenario == "demo":
        generate_demo_scenario(output_dir)
    else:
        generate_full_dataset(output_dir, args.vehicles, args.checkpoints)

    print("\n" + "=" * 60)
    print("✅ Mock data generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
