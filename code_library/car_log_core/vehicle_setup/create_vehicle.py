"""
@snippet: create_vehicle
@mcp: car_log_core
@skill: vehicle_setup
@description: Create a new vehicle with required details
@triggers: create vehicle, add vehicle, new car, register vehicle, add new car
@params: name, make, model, year, vin, license_plate, fuel_type, fuel_capacity_liters, initial_odometer_km
@returns: vehicle_id of created vehicle
@version: 1.0
"""
from carlog_ui.adapters.car_log_core import CarLogCoreAdapter

async def run(
    name: str,
    make: str,
    model: str,
    year: int,
    vin: str,
    license_plate: str,
    fuel_type: str = "Diesel",
    fuel_capacity_liters: float = 50,
    initial_odometer_km: float = 0
):
    """
    Create a new vehicle.

    Args:
        name: Display name for the vehicle
        make: Manufacturer (e.g., Skoda, VW)
        model: Model name (e.g., Octavia, Passat)
        year: Model year
        vin: 17-character VIN (required for Slovak VAT compliance)
        license_plate: License plate (e.g., BA-123CD)
        fuel_type: Diesel, Gasoline, LPG, CNG
        fuel_capacity_liters: Tank capacity in liters
        initial_odometer_km: Starting odometer reading
    """
    adapter = CarLogCoreAdapter()

    # Normalize license plate and VIN to uppercase for consistency
    result = await adapter.call_tool("create_vehicle", {
        "name": name,
        "make": make,
        "model": model,
        "year": year,
        "vin": vin.upper() if vin else vin,
        "license_plate": license_plate.upper() if license_plate else license_plate,
        "fuel_type": fuel_type,
        "fuel_capacity_liters": fuel_capacity_liters,
        "initial_odometer_km": initial_odometer_km
    })

    if not result.success:
        print(f"Error creating vehicle: {result.error}")
        return None

    vehicle_id = result.data.get("vehicle_id")
    print(f"Vehicle created successfully!")
    print(f"  ID: {vehicle_id}")
    print(f"  Name: {name}")
    print(f"  VIN: {vin}")
    print(f"  Plate: {license_plate}")

    return vehicle_id
