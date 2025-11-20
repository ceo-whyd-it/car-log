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

## Testing Scenarios

### Test 1: Standard Registration (Happy Path)
```
Input: "Add my Ford Transit BA-789XY diesel 125000km VIN WVWZZZ3CZDP123456"

Expected Flow:
1. Parse all fields from one message
2. Validate VIN (17 chars, no I/O/Q) ✓
3. Validate license plate (XX-123XX) ✓
4. Show summary
5. Create vehicle
6. Confirm success with next steps

Expected Tools Called:
- car-log-core.list_vehicles (check for duplicates)
- car-log-core.create_vehicle

Success Criteria:
✓ All fields extracted correctly
✓ VIN validation passes
✓ License plate formatted with hyphen
✓ Vehicle created successfully
✓ User prompted for next steps
```

### Test 2: Guided Registration (Conversational)
```
Input: "I need to add my company car"

Expected Flow:
1. Ask for vehicle type → "BMW 5 series"
2. Ask for license plate → "BA456CD" (no hyphen)
3. Auto-correct to "BA-456CD", confirm with user
4. Ask for VIN → "WVWZZZ3CZDP123456"
5. Validate VIN ✓
6. Ask for fuel type → "Gasoline"
7. Ask for odometer → "85000"
8. Show summary, confirm
9. Create vehicle

Success Criteria:
✓ Step-by-step guidance clear
✓ Format auto-correction works
✓ User can review before creation
```

### Test 3: Invalid VIN (Contains I/O/Q)
```
Input: "VIN: WVOZZZ3CZDP123456" (contains O)

Expected Behavior:
❌ Reject VIN
💬 "VIN contains invalid character 'O'. Slovak VINs cannot contain I, O, or Q."
💬 "It might be number 0 (zero) instead of letter O."
💬 "Please double-check and re-enter:"

Success Criteria:
✓ VIN rejected immediately
✓ Clear error message
✓ Helpful suggestion provided
```

### Test 4: Invalid License Plate Format
```
Input: "License plate: BA789XY" (no hyphen)

Expected Behavior:
⚠️ Auto-correct to "BA-789XY"
💬 "License plate format should be BA-789XY (with hyphen). Is this correct?"

Success Criteria:
✓ Auto-correction attempted
✓ User confirmation requested
```

### Test 5: Duplicate License Plate
```
Input: "BA-789XY" (already exists)

Expected Behavior:
❌ Detect duplicate
💬 "Vehicle with license plate BA-789XY already exists:"
💬 [Show existing vehicle details]
💬 "Did you mean to:
     1. Add a different vehicle
     2. View existing vehicle details
     3. Update odometer reading"

Expected Tools Called:
- car-log-core.list_vehicles (returns existing vehicle)

Success Criteria:
✓ Duplicate detected
✓ Existing vehicle shown
✓ Clear options provided
```

### Test 6: Unrealistic Odometer
```
Input: "Odometer: 5000000 km"

Expected Behavior:
⚠️ Flag as suspicious
💬 "Odometer reading seems high (5,000,000 km). That's 125× around Earth!"
💬 "Please confirm reading in kilometers:"

Success Criteria:
✓ Validation triggers on >1,000,000 km
✓ Helpful context provided
```

### Test 7: Fuel Efficiency Expectations
```
Input: Diesel commercial van

Expected Behavior:
💬 "Diesel efficiency: 5-15 L/100km"
💬 "Expected average: 8.5 L/100km for commercial vans"

Success Criteria:
✓ L/100km format used (not km/L)
✓ Reasonable range provided
✓ Context for vehicle type
```

### Test 8: Multi-Vehicle User
```
Input: "Add second vehicle"

Expected Behavior:
1. Show existing vehicles:
   "You have 1 vehicle registered:
    • Ford Transit (BA-789XY) - 125,000 km"
2. Ask "What's the new vehicle?"
3. Continue registration flow

Expected Tools Called:
- car-log-core.list_vehicles (show existing)

Success Criteria:
✓ Existing vehicles displayed
✓ Clear distinction from new vehicle
```

---

## MCP Tool Call Examples

### Example 1: Create Vehicle (Full Data)
```json
// Request
{
  "tool": "car-log-core.create_vehicle",
  "parameters": {
    "name": "Ford Transit Delivery Van",
    "license_plate": "BA-789XY",
    "vin": "WVWZZZ3CZDP123456",
    "make": "Ford",
    "model": "Transit",
    "year": 2022,
    "fuel_type": "Diesel",
    "initial_odometer_km": 125000
  }
}

// Response
{
  "success": true,
  "vehicle_id": "abc-123-def-456",
  "vehicle": {
    "vehicle_id": "abc-123-def-456",
    "name": "Ford Transit Delivery Van",
    "license_plate": "BA-789XY",
    "vin": "WVWZZZ3CZDP123456",
    "make": "Ford",
    "model": "Transit",
    "year": 2022,
    "fuel_type": "Diesel",
    "initial_odometer_km": 125000,
    "current_odometer_km": 125000,
    "total_distance_km": 0,
    "created_at": "2025-11-20T14:30:00Z"
  }
}
```

### Example 2: Check Existing Vehicles
```json
// Request
{
  "tool": "car-log-core.list_vehicles",
  "parameters": {}
}

// Response
{
  "success": true,
  "vehicles": [
    {
      "vehicle_id": "abc-123-def-456",
      "name": "Ford Transit Delivery Van",
      "license_plate": "BA-789XY",
      "current_odometer_km": 125000,
      "total_distance_km": 0
    }
  ]
}
```

---

## Integration Patterns

### Pattern 1: Duplicate Check Before Create
```javascript
// Always check for duplicates first
const existing = await mcp.call("car-log-core.list_vehicles");
const duplicate = existing.vehicles.find(v => v.license_plate === inputPlate);

if (duplicate) {
  // Show duplicate message
} else {
  // Proceed with creation
}
```

### Pattern 2: Progressive Field Collection
```javascript
// Collect required fields first
const required = {
  name: await ask("What kind of vehicle?"),
  license_plate: await ask("License plate (XX-123XX)?"),
  vin: await askWithValidation("VIN (17 chars)?", validateVIN),
  fuel_type: await ask("Fuel type?"),
  initial_odometer_km: await ask("Current odometer (km)?")
};

// Optional fields only if user wants
if (await confirm("Add make/model/year? (optional)")) {
  required.make = await ask("Make?");
  required.model = await ask("Model?");
  required.year = await ask("Year?");
}
```

### Pattern 3: Format Auto-Correction
```javascript
// Auto-correct license plate format
function correctLicensePlate(input) {
  // Remove all hyphens and spaces
  const clean = input.replace(/[-\s]/g, '');

  // Match pattern: 1-2 letters, 3 digits, 2 letters
  const match = clean.match(/^([A-Z]{1,2})(\d{3})([A-Z]{2})$/i);

  if (match) {
    return `${match[1].toUpperCase()}-${match[2]}${match[3].toUpperCase()}`;
  }

  return null; // Invalid format
}
```

---

## Edge Cases Handled

### 1. VIN with Lowercase
```
Input: "wvwzzz3czdp123456"
Output: Convert to uppercase → "WVWZZZ3CZDP123456"
```

### 2. License Plate Variations
```
Input: "BA 789 XY" → "BA-789XY"
Input: "BA789XY" → "BA-789XY"
Input: "ba-789xy" → "BA-789XY"
```

### 3. Fuel Type Aliases
```
Input: "nafta" → "Diesel" (Slovak)
Input: "benzín" → "Gasoline" (Slovak)
Input: "95" → "Gasoline" (octane)
```

### 4. Odometer Variations
```
Input: "125,000" → 125000 (remove comma)
Input: "125 000" → 125000 (remove space)
Input: "125000 km" → 125000 (remove unit)
```

---

**Implementation Status:** 📋 Specification ready, implementation pending

**Estimated Effort:** 2 hours (with MCP tool already functional)

**Dependencies:** `car-log-core.create_vehicle`, `car-log-core.list_vehicles` (both implemented ✅)
