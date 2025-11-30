"""
@snippet: calculate_route
@mcp: geo_routing
@skill: geocode
@description: Calculate driving route and distance between two points
@triggers: calculate route, driving distance, route between, how far
@params: from_coords, to_coords
@returns: distance in km and duration
@version: 1.1

NOTE: geo_routing is an HTTP service (not MCP adapter).
Use urllib to call it directly.
"""

# Example usage:
# from_lat, from_lng = 48.1486, 17.1077  # Bratislava
# to_lat, to_lng = 48.7164, 21.2611      # Košice

import urllib.request
import urllib.parse

geo_url = os.environ.get("GEO_ROUTING_URL", "http://geo-routing:8002")
params = urllib.parse.urlencode({
    "from_lat": from_lat,
    "from_lng": from_lng,
    "to_lat": to_lat,
    "to_lng": to_lng
})

url = f"{geo_url}/route?{params}"

try:
    with urllib.request.urlopen(url, timeout=30) as response:
        result = json.loads(response.read().decode())

    if result.get("success"):
        distance_km = result.get("distance_km", 0)
        duration_min = result.get("duration_minutes", 0)

        print(f"Route calculated:")
        print(f"  Distance: {distance_km:.1f} km")
        print(f"  Duration: {duration_min:.0f} minutes")
        print(f"  Average speed: {distance_km / (duration_min / 60):.0f} km/h")
    else:
        print(f"Route calculation failed: {result.get('error')}")

except Exception as e:
    print(f"Error calculating route: {e}")
