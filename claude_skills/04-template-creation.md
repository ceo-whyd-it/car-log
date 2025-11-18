# Skill 4: Template Creation (GPS Mandatory)

**Purpose:** Create recurring trip templates with GPS coordinates (enables high-confidence matching)

**Priority:** P0

---

## Trigger Words

- "create template", "save this route"
- After reconstruction: "Save this as template?"
- "I make this trip every week"

---

## Workflow

### Step 1: Collect Template Data
```
User: "Save Warehouse Run as template"

Claude: "Creating template 'Warehouse Run'.

Where does it start?"

User: "Bratislava office"

Claude: "Geocoding 'Bratislava office'...
[Calls: geo-routing.geocode_address]

Found 3 matches:
1. Bratislava City Center (48.1486°N, 17.1077°E)
2. Bratislava-Petržalka (48.1234°N, 17.1100°E)
3. Bratislava Airport (48.1702°N, 17.2127°E)

Which location? (1/2/3)"

User: "1"

Claude: "✓ Start: 48.1486°N, 17.1077°E 'Bratislava City Center'

Where does it end?"
```

### Step 2: Calculate Route
```
[After collecting end location]

Claude: "Calculating routes...
[Calls: geo-routing.calculate_route]

3 routes found:
• D1 highway: 395km (4.2 hrs) €12 tolls
• E50: 410km (4.5 hrs) ← Recommended (most direct)
• Local roads: 385km (5.8 hrs)

Which route do you typically take? (1/2/3)"
```

### Step 3: Optional Enhancements
```
Claude: "Template basics set (410km).

Optional enhancements:
• Round trip? (yes/no)
• Typical days? (e.g., Monday, Thursday)
• Business or personal?"

User: "Yes round trip, Monday and Thursday, business"

Claude: "✓ Round trip: 820km total
✓ Days: Monday, Thursday
✓ Purpose: Business"
```

### Step 4: Create Template
```
[Calls: car-log-core.create_template]

✅ Template created!

'Warehouse Run'
• From: 48.1486°N, 17.1077°E 'Bratislava'
• To: 48.7164°N, 21.2611°E 'Košice'
• Distance: 820km (round trip)
• Days: Monday, Thursday
• Purpose: Business
• GPS coordinates saved ← 70% matching weight!

I'll match this template with 90%+ confidence on future trips!"
```

---

## MCP Tools Used

1. **geo-routing.geocode_address** - Get GPS from address (CRITICAL)
2. **geo-routing.calculate_route** - Show route alternatives
3. **car-log-core.create_template** - Save template with GPS mandatory

---

## GPS Mandatory Philosophy

**Why GPS is Required:**
```
Address alone: "Košice" → 3 fuel stations, ambiguous
GPS: 48.7164°N, 21.2611°E → Exact location, 92% confidence match
```

**User Messaging:**
```
"✓ GPS coordinates saved - I can match future trips within 100m accuracy!"
```

---

## Success Criteria

- ✅ GPS coordinates mandatory (validates before saving)
- ✅ Address ambiguity resolved with user selection
- ✅ Route calculation shows alternatives
- ✅ Optional fields enhance matching (days, purpose)

---

**Implementation:** 📋 Spec ready | **Effort:** 3 hours
