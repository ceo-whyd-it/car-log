"""
@snippet: geocode_address
@mcp: geo_routing
@skill: geocode
@description: Convert address to GPS coordinates using OpenStreetMap
@triggers: geocode, address to gps, find coordinates, locate address
@params: address, country_hint
@returns: GPS coordinates and confidence
@version: 1.1

NOTE: geo_routing is an HTTP service (not MCP adapter).
Use urllib to call it directly.
"""

# Example usage:
# address = "Hlavná 45, Bratislava"
# country_hint = "SK"

import urllib.request
import urllib.parse

geo_url = os.environ.get("GEO_ROUTING_URL", "http://geo-routing:8002")
params = urllib.parse.urlencode({
    "address": address,
    "country": country_hint
})

url = f"{geo_url}/geocode?{params}"

try:
    with urllib.request.urlopen(url, timeout=30) as response:
        result = json.loads(response.read().decode())

    if result.get("success"):
        coords = result.get("coordinates", {})
        confidence = result.get("confidence", 0)

        print(f"Geocoding result for: {address}")
        print(f"  Latitude: {coords.get('lat')}")
        print(f"  Longitude: {coords.get('lng')}")
        print(f"  Confidence: {confidence:.0%}")

        # Check for alternatives if ambiguous
        alternatives = result.get("alternatives", [])
        if alternatives:
            print(f"\nAlternative matches ({len(alternatives)}):")
            for i, alt in enumerate(alternatives[:3], 1):
                print(f"  {i}. {alt.get('display_name')}")
    else:
        print(f"Geocoding failed: {result.get('error')}")

except Exception as e:
    print(f"Error geocoding address: {e}")
