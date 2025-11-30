"""
@snippet: match_templates
@mcp: trip_reconstructor
@skill: matching
@description: Match gap between checkpoints to existing route templates
@triggers: match templates, reconstruct trips, find matching routes, gap matching
@params: gap_data, templates
@returns: list of matching proposals with confidence scores
@version: 1.1

NOTE: This code is executed in the agent's code execution environment.
Adapters are available as globals: car_log_core, trip_reconstructor, etc.
DO NOT import adapters - use them directly.
"""

# Example usage:
# checkpoint1_id = "cp-123"
# checkpoint2_id = "cp-456"
# vehicle_id = "vehicle-789"

# Step 1: Get gap analysis
gap_result = await car_log_core.detect_gap(
    checkpoint1_id=checkpoint1_id,
    checkpoint2_id=checkpoint2_id
)

if not gap_result.get('gap_detected'):
    print("No gap detected between these checkpoints.")
else:
    gap_info = gap_result.get('gap_info', {})
    print(f"Gap detected: {gap_info.get('distance_km', 0):.1f} km")

    # Step 2: Get templates for this vehicle
    templates = await car_log_core.list_templates(vehicle_id=vehicle_id)
    template_list = templates.get('templates', [])

    if not template_list:
        print("No templates found. Please create route templates first.")
        print("Templates are reusable routes (e.g., 'Home to Office', 'Warehouse Run')")
    else:
        print(f"Found {len(template_list)} templates to match against")

        # Step 3: Run matching algorithm
        match_result = await trip_reconstructor.match_templates(
            gap_data=gap_info,
            templates=template_list
        )

        proposals = match_result.get('proposals', [])

        if proposals:
            print(f"\nMatching proposals ({len(proposals)}):")
            for i, prop in enumerate(proposals, 1):
                conf = prop.get('confidence', 0)
                name = prop.get('template_name', 'Unknown')
                distance = prop.get('distance_km', 0)

                status = "✓ RECOMMENDED" if conf >= 70 else "⚠ LOW CONFIDENCE"
                print(f"  {i}. {name}")
                print(f"     Distance: {distance:.1f} km | Confidence: {conf:.0f}% [{status}]")
        else:
            print("No matching templates found for this gap.")
            print("Consider creating a new template for this route.")
