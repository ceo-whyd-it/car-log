# Skill 1: Vehicle Setup (Slovak Compliance)

**Purpose:** Guide users through tax-compliant vehicle registration with VIN validation

**Priority:** P0 (Required for MVP)

---

## Trigger Words

- "add vehicle", "register car", "new vehicle", "create vehicle"
- "Ford Transit", "company van", "BMW", "Škoda"
- License plate patterns: "BA-*", "*-123*"
- "I got a new car"

---

## Workflow Steps

### Step 1: Detect Intent

```
User: "I need to add my Ford Transit delivery van"

Claude (activates skill): "I'll help you register your vehicle for tax-compliant mileage tracking. I need a few details:"
```

### Step 2: Collect Vehicle Details

**Required Fields:**
1. **Name** (human-readable, e.g., "Ford Transit Delivery Van")
2. **License Plate** (Slovak format: XX-123XX)
3. **VIN** (17 characters, no I/O/Q - MANDATORY for Slovak VAT Act 2025)
4. **Fuel Type** (Diesel, Gasoline, LPG, Hybrid, Electric)
5. **Initial Odometer** (km when added to system)

**Optional Fields:**
6. Make (e.g., Ford)
7. Model (e.g., Transit)
8. Year (e.g., 2022)

**Conversational Flow:**

```
Claude: "Great! Let's get your Ford Transit registered.

1️⃣ License Plate (format: BA-456CD):
   What's the license plate?"

User: "BA-789XY"

Claude: "✓ BA-789XY

2️⃣ VIN (17 characters, mandatory for tax compliance):
   What's the Vehicle Identification Number?"

User: "WVWZZZ3CZDP123456"

Claude: "✓ VIN validated (17 characters, no I/O/Q)

3️⃣ Fuel Type:
   What fuel does it use?
   • Diesel
   • Gasoline (95/98)
   • LPG
   • Hybrid
   • Electric"

User: "Diesel"

Claude: "✓ Diesel (average efficiency: 8.5 L/100km for commercial vans)

4️⃣ Current Odometer Reading:
   How many kilometers are currently on the odometer?"

User: "125000"

Claude: "✓ 125,000 km

Summary:
• Name: Ford Transit Delivery Van
• Plate: BA-789XY
• VIN: WVWZZZ3CZDP123456
• Fuel: Diesel
• Odometer: 125,000 km

Create this vehicle? (yes/no)"
```

### Step 3: Validation

**VIN Validation:**
```javascript
function validateVIN(vin) {
  // Must be exactly 17 characters
  if (vin.length !== 17) return false;

  // No I, O, Q characters (per ISO 3779)
  if (/[IOQ]/.test(vin)) return false;

  // Only alphanumeric
  if (!/^[A-HJ-NPR-Z0-9]{17}$/.test(vin)) return false;

  return true;
}
```

**License Plate Validation:**
```javascript
function validateLicensePlate(plate) {
  // Slovak format: XX-123XX or X-123XX
  return /^[A-Z]{1,2}-[0-9]{3}[A-Z]{2}$/.test(plate);
}
```

**Error Handling:**
```
User: "INVALID123" (VIN)

Claude: "⚠️ VIN must be exactly 17 characters. Slovak tax law requires a complete VIN for VAT deduction.

Please provide the full 17-character VIN (found on registration or dashboard):"
```

```
User: "BA123CD" (license plate)

Claude: "⚠️ License plate format should be XX-123XX (e.g., BA-456CD).

Please enter with hyphen: BA-123CD"
```

### Step 4: Call MCP Tool

```typescript
// MCP Tool Call
const result = await mcp.call("car-log-core.create_vehicle", {
  name: "Ford Transit Delivery Van",
  license_plate: "BA-789XY",
  vin: "WVWZZZ3CZDP123456",
  make: "Ford",
  model: "Transit",
  year: 2022,
  fuel_type: "Diesel",
  initial_odometer_km: 125000
});
```

### Step 5: Confirmation

```
Claude: "✅ Vehicle registered successfully!

Ford Transit Delivery Van (BA-789XY)
• VIN: WVWZZZ3CZDP123456 ✓ Tax compliant
• Fuel: Diesel (5-15 L/100km expected range)
• Odometer: 125,000 km
• ID: abc-123-def-456

Next steps:
1. Take a photo of your first fuel receipt
2. I'll create checkpoints automatically
3. Track your trips with GPS accuracy

Ready to add your first checkpoint?"
```

---

## MCP Tools Used

### Primary Tool

**`car-log-core.create_vehicle`**

**Input:**
```json
{
  "name": "string",
  "license_plate": "string (XX-123XX)",
  "vin": "string (17 chars, no I/O/Q)",
  "make": "string (optional)",
  "model": "string (optional)",
  "year": "integer (optional)",
  "fuel_type": "enum [Diesel, Gasoline, LPG, Hybrid, Electric]",
  "initial_odometer_km": "integer"
}
```

**Output:**
```json
{
  "success": true,
  "vehicle_id": "uuid",
  "vehicle": {
    "vehicle_id": "uuid",
    "name": "string",
    "license_plate": "string",
    "vin": "string",
    "fuel_type": "string",
    "initial_odometer_km": 125000,
    "current_odometer_km": 125000,
    "total_distance_km": 0,
    "created_at": "ISO 8601"
  }
}
```

### Secondary Tool (Check Existing)

**`car-log-core.list_vehicles`**

Used to:
- Check for duplicate license plates
- Show existing vehicles if user has multiple

---

## Error Scenarios

### 1. Duplicate License Plate

```
Claude: "⚠️ Vehicle with license plate BA-789XY already exists:

Ford Transit (125,000 km)

Did you mean to:
1. Add a different vehicle
2. View existing vehicle details
3. Update odometer reading"
```

### 2. Invalid VIN with I/O/Q

```
User: "WVOZZZ3CZDP123456" (contains O)

Claude: "⚠️ VIN contains invalid character 'O'. Slovak VINs cannot contain I, O, or Q (to avoid confusion with 1 and 0).

Please double-check the VIN - it might be:
• Number 0 (zero) instead of letter O
• Letter I instead of number 1

Correct VIN:"
```

### 3. Unrealistic Odometer

```
User: "999999999"

Claude: "⚠️ Odometer reading seems unusually high (999,999,999 km). Earth's circumference is ~40,000 km!

Please confirm odometer reading in kilometers:"
```

---

## Slovak Compliance Features

### VIN Validation (MANDATORY)

**Why:** Slovak VAT Act 2025 requires VIN for fuel cost deduction

**Validation:**
- Exactly 17 characters
- No I, O, Q letters (ISO 3779 standard)
- Alphanumeric only

**User Message:**
```
"✓ VIN validated - compliant with Slovak VAT Act 2025"
```

### L/100km Format

**Why:** European standard (not km/L)

**Display:**
```
"Expected fuel efficiency: 8.5 L/100km (Diesel commercial van)"
```

### License Plate Format

**Pattern:** XX-123XX (2 letters, hyphen, 3 digits, 2 letters)

**Examples:**
- BA-456CD (Bratislava)
- KE-789XY (Košice)
- TT-123AB (Trnava)

---

## Example Conversations

### Quick Registration

```
User: "Add BA-789XY Ford Transit diesel 125000km VIN WVWZZZ3CZDP123456"

Claude: "✓ Got it! Let me register:
• Ford Transit
• BA-789XY
• Diesel
• 125,000 km
• VIN: WVWZZZ3CZDP123456 ✓

[creates vehicle]

✅ Registered! Ready to track trips."
```

### Guided Registration

```
User: "I need to add my company car"

Claude: "I'll help! What kind of vehicle?"

User: "BMW 5 series"

Claude: "Great! What's the license plate?"

User: "BA 456 CD"

Claude: "License plate format should be BA-456CD (with hyphen). Is this correct: BA-456CD?"

User: "Yes"

Claude: "✓ BA-456CD

What's the VIN (17 characters, found on registration)?"

[continues...]
```

---

## Best Practices

### 1. Clear Slovak Compliance Messaging

Always explain WHY fields are required:
```
"VIN is mandatory for Slovak tax deduction (VAT Act 2025)"
```

### 2. Format Hints

Show format before asking:
```
"License plate (format: BA-456CD):"
```

### 3. Validation Feedback

Immediate feedback on validation:
```
"✓ VIN validated"
"⚠️ License plate format incorrect"
```

### 4. Fuel Efficiency Context

Provide expected ranges:
```
"Diesel efficiency: 5-15 L/100km
Your 8.5 L/100km is normal for commercial vans"
```

### 5. Progressive Disclosure

Required fields first, optional fields if user wants:
```
"Vehicle registered! Want to add make/model/year? (optional)"
```

---

## Success Criteria

- ✅ VIN validation prevents invalid entries
- ✅ License plate format enforced (XX-123XX)
- ✅ Slovak compliance messaging clear
- ✅ L/100km format used (not km/L)
- ✅ Duplicate vehicle detection
- ✅ Conversational flow (not form-like)
- ✅ Error messages are helpful, not cryptic

---

**Implementation Status:** 📋 Specification ready, implementation pending

**Estimated Effort:** 2-3 hours (with MCP tool already functional)

**Dependencies:** `car-log-core.create_vehicle` tool (already implemented ✅)
