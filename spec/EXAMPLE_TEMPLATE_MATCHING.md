# Example: Template Matching with Confidence Scores

## Scenario: 820 km Gap Between Refuel Stops

### Input Data

**Gap Analysis:**
```json
{
  "distance_km": 820,
  "days": 4,
  "start_checkpoint": {
    "checkpoint_id": "ckpt-start",
    "datetime": "2025-11-04T08:00:00Z",
    "odometer_km": 50000,
    "location": {
      "coords": {"latitude": 48.1486, "longitude": 17.1077},
      "address": "Bratislava, OMV Fuel Station"
    }
  },
  "end_checkpoint": {
    "checkpoint_id": "ckpt-end",
    "datetime": "2025-11-08T18:00:00Z",
    "odometer_km": 50820,
    "location": {
      "coords": {"latitude": 48.1486, "longitude": 17.1077},
      "address": "Bratislava, OMV Fuel Station"
    }
  }
}
```

**Available Templates:**
```json
[
  {
    "template_id": "tmpl-warehouse",
    "name": "Warehouse Run",
    "from_coords": {"lat": 48.1486, "lng": 17.1077},
    "from_address": "Bratislava",
    "to_coords": {"lat": 48.7164, "lng": 21.2611},
    "to_address": "Košice, Warehouse District",
    "distance_km": 410,
    "is_round_trip": true,
    "typical_days": ["Monday", "Thursday"],
    "purpose": "business",
    "business_description": "Warehouse pickup and delivery"
  },
  {
    "template_id": "tmpl-office",
    "name": "Office Commute",
    "from_coords": {"lat": 48.1486, "lng": 17.1077},
    "from_address": "Bratislava, Home",
    "to_coords": {"lat": 48.1580, "lng": 17.1200},
    "to_address": "Bratislava, Office Park",
    "distance_km": 5,
    "is_round_trip": true,
    "typical_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "purpose": "business"
  },
  {
    "template_id": "tmpl-client",
    "name": "Client Visit - Žilina",
    "from_coords": {"lat": 48.1486, "lng": 17.1077},
    "from_address": "Bratislava",
    "to_coords": {"lat": 49.2233, "lng": 18.7397},
    "to_address": "Žilina, Client Office",
    "distance_km": 200,
    "is_round_trip": false,
    "typical_days": ["Wednesday"],
    "purpose": "business",
    "business_description": "Client consultation"
  }
]
```

## Template Matching Results

### Match 1: Warehouse Run ✓

**Start Point Match (Bratislava → Template FROM):**
```
GPS Match:
  Distance: 0 meters
  Score: 100 points

Address Match:
  Gap: "Bratislava, OMV Fuel Station"
  Template: "Bratislava"
  Score: 52 points (city match + partial string match)

Hybrid Score:
  GPS contribution: 100 × 0.7 = 70.0
  Address contribution: 52 × 0.3 = 15.6
  Base score: 85.6

Bonuses:
  Day bonus: +10 (Monday matches typical_days)
  Distance bonus: 0 (no template distance for start point)

TOTAL: 95.6 points
```

**End Point Match (Bratislava → Template FROM, since round trip):**
```
GPS Match:
  Distance: 0 meters
  Score: 100 points

Address Match:
  Gap: "Bratislava, OMV Fuel Station"
  Template: "Bratislava"
  Score: 52 points

Hybrid Score:
  GPS contribution: 100 × 0.7 = 70.0
  Address contribution: 52 × 0.3 = 15.6
  Base score: 85.6

Bonuses:
  Day bonus: 0 (Friday not in typical_days)
  Distance bonus: 0

TOTAL: 85.6 points
```

**Average Confidence: 90.6%** ✓ (above 70% threshold)

**Reconstruction Proposal:**
```
Template: Warehouse Run
One-way distance: 410 km
Round trip: YES → 820 km effective distance
Number of trips: 820 / 820 = 1 trip
Coverage: 820 / 820 = 100%
Quality: EXCELLENT
```

### Match 2: Office Commute ⚠

**Start Point Match:**
```
GPS Match:
  Distance: 13 meters (extremely close)
  Score: 100 points

Address Match:
  Gap: "Bratislava, OMV Fuel Station"
  Template: "Bratislava, Home"
  Score: 65 points (same city, different location)

Hybrid Score: 100 × 0.7 + 65 × 0.3 = 89.5
Bonuses: +10 (Monday matches typical_days)
TOTAL: 99.5 points
```

**End Point Match (Bratislava → Template FROM):**
```
GPS Match: 100 points (0m distance)
Address Match: 65 points
Hybrid Score: 89.5
Bonuses: 0
TOTAL: 89.5 points
```

**Average Confidence: 94.5%** ✓ (above 70% threshold)

**BUT: Reconstruction fails due to distance mismatch**
```
Template: Office Commute
Effective distance: 5 × 2 = 10 km (round trip)
Number of trips: 820 / 10 = 82 trips
Coverage: 820 / 820 = 100%

⚠ WARNING: 82 office commutes in 4 days is unrealistic
This template matches geographically but doesn't explain the gap.
```

### Match 3: Client Visit - Žilina ✗

**Start Point Match (Bratislava):**
```
GPS Match: 100 points (0m)
Address Match: 52 points
Hybrid Score: 85.6
TOTAL: 85.6 points
```

**End Point Match (Bratislava → Template TO = Žilina):**
```
GPS Match:
  Distance: 120,824 meters (120 km)
  Score: 0 points (> 5 km threshold)

Address Match:
  Gap: "Bratislava, OMV Fuel Station"
  Template: "Žilina, Client Office"
  Score: 0 points (different cities)

Hybrid Score: 0 × 0.7 + 0 × 0.3 = 0
TOTAL: 0 points
```

**Average Confidence: 42.8%** ✗ (below 70% threshold)

**Result: REJECTED** (confidence too low)

## Final Reconstruction Proposal

```json
{
  "success": true,
  "gap_distance_km": 820,
  "templates_evaluated": 3,
  "templates_matched": 1,
  "confidence_threshold": 70,

  "matched_templates": [
    {
      "template_id": "tmpl-warehouse",
      "template_name": "Warehouse Run",
      "confidence_score": 90.6,
      "start_match": {
        "score": 95.6,
        "distance_meters": 0,
        "gps_score": 100,
        "address_score": 52
      },
      "end_match": {
        "score": 85.6,
        "distance_meters": 0,
        "gps_score": 100,
        "address_score": 52
      }
    }
  ],

  "reconstruction_proposal": {
    "has_proposal": true,
    "proposed_trips": [
      {
        "template_id": "tmpl-warehouse",
        "template_name": "Warehouse Run",
        "confidence_score": 90.6,
        "num_trips": 1,
        "distance_km": 410,
        "is_round_trip": true,
        "total_distance_km": 820
      }
    ],
    "gap_distance_km": 820,
    "reconstructed_km": 820,
    "remaining_km": 0,
    "coverage_percent": 100,
    "reconstruction_quality": "excellent"
  }
}
```

## User Presentation

```
🚗 Gap Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
From: Nov 4, 08:00 @ Bratislava
To:   Nov 8, 18:00 @ Bratislava
Distance: 820 km over 4 days

📋 Reconstruction Proposal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Warehouse Run (1 trip, 90.6% confidence)
  Bratislava → Košice → Bratislava
  410 km × 2 (round trip) = 820 km
  Business trip: Warehouse pickup and delivery

Coverage: 820 / 820 km (100%) - EXCELLENT

Would you like to create these trips?
[Create Trips] [Edit] [Dismiss]
```

## Key Insights

1. **GPS is critical:** Templates need accurate GPS coordinates (70% of score)
2. **Address helps:** Even partial address matches improve confidence (30% of score)
3. **Distance matters:** Warehouse Run fits perfectly (820 km)
4. **Bonuses count:** Day-of-week bonus added +10 points to start match
5. **Quality filtering:** Office Commute rejected despite high confidence due to unrealistic trip count

## Confidence Score Breakdown

| Template | Start Match | End Match | Avg | Status | Reason |
|----------|-------------|-----------|-----|--------|--------|
| Warehouse Run | 95.6% | 85.6% | **90.6%** | ✓ MATCHED | Perfect GPS + distance fit |
| Office Commute | 99.5% | 89.5% | 94.5% | ⚠ FILTERED | Unrealistic trip count (82 trips) |
| Client Visit | 85.6% | 0% | 42.8% | ✗ REJECTED | End point doesn't match |

## Why This Works

The hybrid GPS (70%) + address (30%) algorithm successfully:

1. **Identifies the correct template:** Warehouse Run matches both endpoints
2. **Filters false positives:** Office Commute has high confidence but wrong distance
3. **Rejects poor matches:** Client Visit fails end point match
4. **Achieves 100% coverage:** 1 round trip perfectly explains the 820 km gap
5. **Provides confidence metrics:** User can trust the 90.6% confidence score

This demonstrates the power of the hybrid matching algorithm for real-world trip reconstruction scenarios.
