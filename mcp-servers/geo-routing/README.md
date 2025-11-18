# geo-routing MCP Server

MCP server providing geocoding and route calculation via OpenStreetMap (Nominatim + OSRM).

## Features

- **geocode_address**: Convert address text to GPS coordinates with ambiguity handling
- **reverse_geocode**: Convert GPS coordinates to human-readable address
- **calculate_route**: Calculate routes between two GPS coordinates

## Installation

```bash
npm install
```

## Configuration

Environment variables:

- `OSRM_BASE_URL`: OSRM API endpoint (default: https://router.project-osrm.org)
- `NOMINATIM_BASE_URL`: Nominatim API endpoint (default: https://nominatim.openstreetmap.org)
- `CACHE_TTL_HOURS`: Cache TTL in hours (default: 24)

## Usage

### As MCP Server

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "geo-routing": {
      "command": "node",
      "args": ["/path/to/mcp-servers/geo-routing/index.js"],
      "env": {
        "OSRM_BASE_URL": "https://router.project-osrm.org",
        "NOMINATIM_BASE_URL": "https://nominatim.openstreetmap.org",
        "CACHE_TTL_HOURS": "24"
      }
    }
  }
}
```

### Running Tests

```bash
npm test
```

## Tools

### 1. geocode_address

Convert address text to GPS coordinates with ambiguity handling.

**Input:**
```json
{
  "address": "Košice",
  "country_hint": "SK"
}
```

**Output (Ambiguous - confidence < 0.7):**
```json
{
  "success": true,
  "coordinates": {
    "latitude": 48.7164,
    "longitude": 21.2611
  },
  "normalized_address": "Košice, Slovakia",
  "confidence": 0.65,
  "alternatives": [
    {
      "address": "Košice city center",
      "coordinates": { "lat": 48.7178, "lng": 21.2575 },
      "confidence": 0.65,
      "type": "city"
    },
    {
      "address": "Košice-Západ (west district)",
      "coordinates": { "lat": 48.6900, "lng": 21.1900 },
      "confidence": 0.55,
      "type": "district"
    },
    {
      "address": "Košice-Sever (north district)",
      "coordinates": { "lat": 48.7400, "lng": 21.2500 },
      "confidence": 0.50,
      "type": "district"
    }
  ]
}
```

**Output (Clear - confidence >= 0.7):**
```json
{
  "success": true,
  "coordinates": {
    "latitude": 48.1486,
    "longitude": 17.1077
  },
  "normalized_address": "Hlavná 45, 811 01 Bratislava, Slovakia",
  "confidence": 0.98,
  "alternatives": []
}
```

### 2. reverse_geocode

Convert GPS coordinates to human-readable address.

**Input:**
```json
{
  "latitude": 48.1486,
  "longitude": 17.1077
}
```

**Output:**
```json
{
  "address": {
    "street": "Hlavná",
    "house_number": "45",
    "city": "Bratislava",
    "postal_code": "811 01",
    "country": "Slovakia",
    "formatted": "Hlavná 45, 811 01 Bratislava, Slovakia"
  },
  "poi": "Shell Bratislava West"
}
```

### 3. calculate_route

Calculate route between two GPS coordinates.

**Input:**
```json
{
  "from_coords": { "lat": 48.1486, "lng": 17.1077 },
  "to_coords": { "lat": 48.7164, "lng": 21.2611 },
  "alternatives": 1,
  "vehicle": "car"
}
```

**Output:**
```json
{
  "routes": [
    {
      "distance_km": 410.5,
      "duration_hours": 4.2,
      "via": "via D1, E571",
      "route_type": "highway",
      "waypoints": [
        {
          "name": "D1",
          "latitude": 48.15,
          "longitude": 17.20
        },
        {
          "name": "E571",
          "latitude": 48.50,
          "longitude": 19.00
        }
      ]
    }
  ]
}
```

## Ambiguity Handling

When geocoding returns confidence < 0.7, the response includes up to 3 alternatives for the user to choose from. This is common for:

- City names only (e.g., "Košice")
- Ambiguous street names
- Multiple locations with same name

## Caching

All API calls are cached for 24 hours (configurable) to:
- Reduce API load
- Improve response times
- Respect Nominatim rate limits

Cache key format:
- Geocoding: `geocode:{address}:{country_hint}`
- Reverse: `reverse:{lat},{lng}`
- Routing: `route:{from_lat},{from_lng}:{to_lat},{to_lng}:{alternatives}:{vehicle}`

## Rate Limiting

**Nominatim**: Requires 1 request per second. The MCP server handles caching but does not enforce rate limiting (handled by caller).

**OSRM**: No strict rate limits for public instance.

## Testing

The test suite verifies:

1. Clear address geocoding (Bratislava)
2. Ambiguous address geocoding (Košice → returns 3 alternatives)
3. Reverse geocoding
4. Route calculation (Bratislava → Košice ≈ 410 km via D1)

Expected test output:
```
=== Test 2: Ambiguous Address Geocoding ===
Address: "Košice"
✅ Success
   Top result: Košice, Slovakia
   Coordinates: 48.7164, 21.2611
   Confidence: 0.65
   Should have confidence < 0.7: ✅

   Alternatives (should return 3):
   1. Košice city center
      Type: city, Confidence: 0.65
      Coords: 48.7178, 21.2575
   2. Košice-Západ (west district)
      Type: district, Confidence: 0.55
      Coords: 48.6900, 21.1900
   3. Košice-Sever (north district)
      Type: district, Confidence: 0.50
      Coords: 48.7400, 21.2500
```

## Implementation Notes

### Confidence Scoring

Confidence is calculated based on:
1. Nominatim's `importance` score (0-1)
2. Place type specificity:
   - House/building: 1.0
   - Street: 0.95
   - POI: 0.9
   - City: 0.7
   - District: 0.6
   - Region: 0.5

Formula: `confidence = (importance + typeScore) / 2`

### Route Type Detection

Routes are classified as:
- **highway**: Contains D-roads (D1, D2, etc.) or E-roads (E50, E571, etc.)
- **mixed**: Contains regional roads (R-roads)
- **local**: No major roads

### OSRM Coordinate Order

OSRM uses `longitude,latitude` (not `latitude,longitude`). The server handles this conversion automatically.

## Line Count

- `index.js`: 586 lines
- `test.js`: 295 lines
- `package.json`: 18 lines
- `README.md`: 241 lines

Total: ~1140 lines
