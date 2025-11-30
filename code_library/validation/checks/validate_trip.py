"""
@snippet: validate_trip
@mcp: validation
@skill: checks
@description: Validate a trip for Slovak tax compliance
@triggers: validate trip, check trip, verify trip, trip validation
@params: trip_id or trip_data
@returns: validation results with pass/fail status
@version: 1.1

NOTE: This code is executed in the agent's code execution environment.
Adapters are available as globals: car_log_core, validation, etc.
DO NOT import adapters - use them directly.
"""

# Example usage:
# trip_id = "trip-123"

# Validate a trip
result = await validation.validate_trip(trip_id=trip_id)

if result.get('success'):
    valid = result.get('valid', False)

    print(f"Trip Validation: {'PASSED' if valid else 'FAILED'}")
    print("=" * 40)

    checks = result.get('checks', {})
    for check_name, check_result in checks.items():
        status = "✓ PASS" if check_result.get('passed') else "✗ FAIL"
        message = check_result.get('message', '')
        print(f"  [{status}] {check_name}")
        if message:
            print(f"          {message}")

    warnings = result.get('warnings', [])
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  ⚠ {warning}")

    if valid:
        print("\nTrip is compliant with Slovak VAT Act 2025 requirements.")
    else:
        print("\nTrip has compliance issues that need to be addressed.")
else:
    print(f"Error validating trip: {result.get('error')}")
