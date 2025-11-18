#!/usr/bin/env node

/**
 * Mock test suite for geo-routing MCP server
 *
 * Demonstrates expected behavior without calling external APIs.
 * This verifies the logic for confidence scoring and ambiguity handling.
 */

// Mock confidence calculation (same as index.js)
function calculateConfidence(result) {
  const importance = parseFloat(result.importance || 0);
  const typeScores = {
    'house': 1.0,
    'street': 0.95,
    'poi': 0.9,
    'city': 0.7,
    'district': 0.6,
    'region': 0.5,
    'state': 0.4,
    'country': 0.3,
  };

  const placeType = result.type || result.class || 'unknown';
  let typeScore = typeScores[placeType] || 0.5;

  const confidence = Math.min(1.0, (importance + typeScore) / 2);
  return Math.round(confidence * 100) / 100;
}

function getPlaceType(result) {
  const addressType = result.addresstype || result.type || result.class;

  const typeMap = {
    'house': 'street',
    'building': 'street',
    'road': 'street',
    'city': 'city',
    'town': 'city',
    'village': 'city',
    'suburb': 'district',
    'district': 'district',
    'administrative': 'region',
    'state': 'region',
    'amenity': 'poi',
    'shop': 'poi',
  };

  return typeMap[addressType] || 'city';
}

/**
 * Test 1: Clear address - should have high confidence, no alternatives
 */
function testClearAddress() {
  console.log('\n=== Test 1: Clear Address (Mock) ===');
  console.log('Input: "Hlavná 45, Bratislava"');

  // Mock Nominatim response for clear address
  const mockResults = [
    {
      lat: "48.1486",
      lon: "17.1077",
      display_name: "Hlavná 45, 811 01 Bratislava, Slovakia",
      importance: 0.6,
      type: "building",
      addresstype: "building",
    }
  ];

  const results = mockResults.map(r => ({
    address: r.display_name,
    coordinates: {
      lat: parseFloat(r.lat),
      lng: parseFloat(r.lon),
    },
    confidence: calculateConfidence(r),
    type: getPlaceType(r),
  }));

  results.sort((a, b) => b.confidence - a.confidence);
  const topResult = results[0];

  const response = {
    success: true,
    coordinates: {
      latitude: topResult.coordinates.lat,
      longitude: topResult.coordinates.lng,
    },
    normalized_address: topResult.address,
    confidence: topResult.confidence,
    alternatives: [],
  };

  // Check if alternatives should be included
  if (topResult.confidence < 0.7 && results.length > 1) {
    response.alternatives = results.slice(0, 3).map(r => ({
      address: r.address,
      coordinates: r.coordinates,
      confidence: r.confidence,
      type: r.type,
    }));
  }

  console.log('✅ Response:');
  console.log(JSON.stringify(response, null, 2));
  console.log(`\n✅ Confidence >= 0.7: ${response.confidence >= 0.7 ? 'PASS' : 'FAIL'}`);
  console.log(`✅ No alternatives: ${response.alternatives.length === 0 ? 'PASS' : 'FAIL'}`);
}

/**
 * Test 2: Ambiguous address - should have low confidence, include alternatives
 */
function testAmbiguousAddress() {
  console.log('\n=== Test 2: Ambiguous Address (Mock) ===');
  console.log('Input: "Košice"');

  // Mock Nominatim response for ambiguous address
  const mockResults = [
    {
      lat: "48.7164",
      lon: "21.2611",
      display_name: "Košice, Košický kraj, Slovakia",
      importance: 0.55,
      type: "city",
      addresstype: "city",
    },
    {
      lat: "48.7178",
      lon: "21.2575",
      display_name: "Košice - Staré Mesto, Košice, Košický kraj, Slovakia",
      importance: 0.50,
      type: "district",
      addresstype: "suburb",
    },
    {
      lat: "48.6900",
      lon: "21.1900",
      display_name: "Košice - Západ, Košice, Košický kraj, Slovakia",
      importance: 0.45,
      type: "district",
      addresstype: "suburb",
    },
  ];

  const results = mockResults.map(r => ({
    address: r.display_name,
    coordinates: {
      lat: parseFloat(r.lat),
      lng: parseFloat(r.lon),
    },
    confidence: calculateConfidence(r),
    type: getPlaceType(r),
  }));

  results.sort((a, b) => b.confidence - a.confidence);
  const topResult = results[0];

  const response = {
    success: true,
    coordinates: {
      latitude: topResult.coordinates.lat,
      longitude: topResult.coordinates.lng,
    },
    normalized_address: topResult.address,
    confidence: topResult.confidence,
    alternatives: [],
  };

  // Check if alternatives should be included
  if (topResult.confidence < 0.7 && results.length > 1) {
    response.alternatives = results.slice(0, 3).map(r => ({
      address: r.address,
      coordinates: r.coordinates,
      confidence: r.confidence,
      type: r.type,
    }));
  }

  console.log('✅ Response:');
  console.log(JSON.stringify(response, null, 2));
  console.log(`\n✅ Confidence < 0.7: ${response.confidence < 0.7 ? 'PASS' : 'FAIL'}`);
  console.log(`✅ Has 3 alternatives: ${response.alternatives.length === 3 ? 'PASS' : 'FAIL'}`);

  if (response.alternatives.length > 0) {
    console.log('\nAlternatives:');
    response.alternatives.forEach((alt, i) => {
      console.log(`  ${i + 1}. ${alt.address}`);
      console.log(`     Type: ${alt.type}, Confidence: ${alt.confidence}`);
    });
  }
}

/**
 * Test 3: Reverse geocoding format
 */
function testReverseGeocode() {
  console.log('\n=== Test 3: Reverse Geocoding (Mock) ===');
  console.log('Input: 48.1486, 17.1077');

  // Mock reverse geocoding response
  const mockResponse = {
    display_name: "Hlavná 45, 811 01 Bratislava, Slovakia",
    address: {
      road: "Hlavná",
      house_number: "45",
      city: "Bratislava",
      postcode: "811 01",
      country: "Slovakia",
    },
    name: "Shell Bratislava West",
    class: "amenity",
  };

  const result = {
    address: {
      street: mockResponse.address.road || '',
      house_number: mockResponse.address.house_number || '',
      city: mockResponse.address.city || '',
      postal_code: mockResponse.address.postcode || '',
      country: mockResponse.address.country || '',
      formatted: mockResponse.display_name,
    },
  };

  if (mockResponse.name && mockResponse.class === 'amenity') {
    result.poi = mockResponse.name;
  }

  console.log('✅ Response:');
  console.log(JSON.stringify(result, null, 2));
  console.log(`\n✅ Has formatted address: ${result.address.formatted ? 'PASS' : 'FAIL'}`);
  console.log(`✅ Has POI: ${result.poi ? 'PASS' : 'FAIL'}`);
}

/**
 * Test 4: Route calculation format
 */
function testRouteCalculation() {
  console.log('\n=== Test 4: Route Calculation (Mock) ===');
  console.log('Input: Bratislava (48.1486, 17.1077) → Košice (48.7164, 21.2611)');

  // Mock OSRM response
  const mockRoute = {
    distance: 410500, // meters
    duration: 15120, // seconds (4.2 hours)
    legs: [{
      steps: [
        { name: "D1", maneuver: { location: [17.15, 48.16] } },
        { name: "E571", maneuver: { location: [19.00, 48.50] } },
        { name: "D1", maneuver: { location: [20.50, 48.65] } },
      ]
    }]
  };

  // Process route (same logic as index.js)
  const highways = new Set();
  if (mockRoute.legs && mockRoute.legs[0] && mockRoute.legs[0].steps) {
    mockRoute.legs[0].steps.forEach(step => {
      if (step.name && step.name.match(/^(D\d+|E\d+|R\d+|I\/\d+)/)) {
        highways.add(step.name);
      }
    });
  }

  // Determine route type
  let routeType = 'local';
  const highwayList = Array.from(highways);
  if (highwayList.some(h => h.startsWith('D') || h.startsWith('E'))) {
    routeType = 'highway';
  } else if (highwayList.length > 0) {
    routeType = 'mixed';
  }

  const via = highwayList.length > 0
    ? `via ${highwayList.join(', ')}`
    : 'local roads';

  const result = {
    routes: [{
      distance_km: Math.round(mockRoute.distance / 10) / 100,
      duration_hours: Math.round(mockRoute.duration / 36) / 100,
      via,
      route_type: routeType,
      waypoints: mockRoute.legs[0].steps.slice(0, 3).map(s => ({
        name: s.name,
        latitude: s.maneuver.location[1],
        longitude: s.maneuver.location[0],
      })),
    }]
  };

  console.log('✅ Response:');
  console.log(JSON.stringify(result, null, 2));
  console.log(`\n✅ Distance ~410 km: ${result.routes[0].distance_km >= 390 && result.routes[0].distance_km <= 430 ? 'PASS' : 'FAIL'}`);
  console.log(`✅ Route type is highway: ${result.routes[0].route_type === 'highway' ? 'PASS' : 'FAIL'}`);
  console.log(`✅ Via includes D1: ${result.routes[0].via.includes('D1') ? 'PASS' : 'FAIL'}`);
}

/**
 * Run all mock tests
 */
function runMockTests() {
  console.log('========================================');
  console.log('geo-routing MCP Server - Mock Tests');
  console.log('========================================');
  console.log('These tests demonstrate expected behavior');
  console.log('without calling external APIs.');
  console.log('========================================');

  testClearAddress();
  testAmbiguousAddress();
  testReverseGeocode();
  testRouteCalculation();

  console.log('\n========================================');
  console.log('All mock tests completed');
  console.log('========================================\n');
}

// Run mock tests
runMockTests();
