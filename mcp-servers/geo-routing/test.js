#!/usr/bin/env node

/**
 * Test suite for geo-routing MCP server
 *
 * Tests:
 * 1. Clear address geocoding (Bratislava)
 * 2. Ambiguous address geocoding (Košice - should return alternatives)
 * 3. Reverse geocoding
 * 4. Route calculation (Bratislava → Košice, should be ~410 km via D1)
 */

import axios from 'axios';

const NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org';
const OSRM_BASE_URL = 'https://router.project-osrm.org';

// Axios instances
const nominatimClient = axios.create({
  baseURL: NOMINATIM_BASE_URL,
  headers: {
    'User-Agent': 'CarLog/1.0 (MCP Server Test)',
  },
  timeout: 10000,
});

const osrmClient = axios.create({
  baseURL: OSRM_BASE_URL,
  timeout: 15000,
});

// Utility functions (copied from index.js for testing)
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
 * Test 1: Clear address geocoding
 */
async function testClearAddress() {
  console.log('\n=== Test 1: Clear Address Geocoding ===');
  console.log('Address: "Hlavná 45, Bratislava"');

  try {
    const response = await nominatimClient.get('/search', {
      params: {
        q: 'Hlavná 45, Bratislava',
        format: 'json',
        addressdetails: 1,
        countrycodes: 'sk',
        limit: 5,
      },
    });

    if (response.data.length === 0) {
      console.log('❌ No results found');
      return;
    }

    const result = response.data[0];
    const confidence = calculateConfidence(result);

    console.log('✅ Success');
    console.log(`   Coordinates: ${result.lat}, ${result.lon}`);
    console.log(`   Confidence: ${confidence}`);
    console.log(`   Address: ${result.display_name}`);
    console.log(`   Should have confidence >= 0.7: ${confidence >= 0.7 ? '✅' : '❌'}`);

  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
}

/**
 * Test 2: Ambiguous address geocoding
 */
async function testAmbiguousAddress() {
  console.log('\n=== Test 2: Ambiguous Address Geocoding ===');
  console.log('Address: "Košice"');

  try {
    const response = await nominatimClient.get('/search', {
      params: {
        q: 'Košice',
        format: 'json',
        addressdetails: 1,
        limit: 5,
      },
    });

    if (response.data.length === 0) {
      console.log('❌ No results found');
      return;
    }

    // Process results
    const results = response.data.map(r => ({
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

    console.log('✅ Success');
    console.log(`   Top result: ${topResult.address}`);
    console.log(`   Coordinates: ${topResult.coordinates.lat}, ${topResult.coordinates.lng}`);
    console.log(`   Confidence: ${topResult.confidence}`);
    console.log(`   Should have confidence < 0.7: ${topResult.confidence < 0.7 ? '✅' : '❌'}`);

    if (topResult.confidence < 0.7 && results.length > 1) {
      console.log('\n   Alternatives (should return 3):');
      results.slice(0, 3).forEach((alt, i) => {
        console.log(`   ${i + 1}. ${alt.address}`);
        console.log(`      Type: ${alt.type}, Confidence: ${alt.confidence}`);
        console.log(`      Coords: ${alt.coordinates.lat}, ${alt.coordinates.lng}`);
      });
    } else {
      console.log('   ❌ No alternatives returned (expected alternatives)');
    }

  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
}

/**
 * Test 3: Reverse geocoding
 */
async function testReverseGeocode() {
  console.log('\n=== Test 3: Reverse Geocoding ===');
  console.log('Coordinates: 48.1486, 17.1077 (Bratislava city center)');

  try {
    const response = await nominatimClient.get('/reverse', {
      params: {
        lat: 48.1486,
        lon: 17.1077,
        format: 'json',
        addressdetails: 1,
      },
    });

    if (!response.data) {
      console.log('❌ No address found');
      return;
    }

    const data = response.data;
    const addr = data.address || {};

    console.log('✅ Success');
    console.log(`   Formatted: ${data.display_name}`);
    console.log(`   City: ${addr.city || addr.town || addr.village || 'N/A'}`);
    console.log(`   Country: ${addr.country || 'N/A'}`);
    console.log(`   Postcode: ${addr.postcode || 'N/A'}`);

  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
}

/**
 * Test 4: Route calculation (Bratislava → Košice)
 */
async function testRouteCalculation() {
  console.log('\n=== Test 4: Route Calculation ===');
  console.log('Route: Bratislava → Košice');

  try {
    // Bratislava: 48.1486, 17.1077
    // Košice: 48.7164, 21.2611
    const fromLng = 17.1077;
    const fromLat = 48.1486;
    const toLng = 21.2611;
    const toLat = 48.7164;

    const coords = `${fromLng},${fromLat};${toLng},${toLat}`;

    const response = await osrmClient.get(`/route/v1/car/${coords}`, {
      params: {
        overview: 'full',
        alternatives: 'false',
        steps: 'true',
        annotations: 'false',
      },
    });

    if (!response.data || response.data.code !== 'Ok') {
      console.log('❌ Route calculation failed');
      return;
    }

    const route = response.data.routes[0];
    const distanceKm = Math.round(route.distance / 10) / 100;
    const durationHours = Math.round(route.duration / 36) / 100;

    // Extract highway names
    const highways = new Set();
    if (route.legs && route.legs[0] && route.legs[0].steps) {
      route.legs[0].steps.forEach(step => {
        if (step.name && step.name.match(/^(D\d+|E\d+|R\d+|I\/\d+)/)) {
          highways.add(step.name);
        }
      });
    }

    console.log('✅ Success');
    console.log(`   Distance: ${distanceKm} km`);
    console.log(`   Duration: ${durationHours} hours`);
    console.log(`   Via: ${Array.from(highways).join(', ') || 'local roads'}`);
    console.log(`   Should be ~410 km via D1: ${distanceKm >= 390 && distanceKm <= 430 ? '✅' : '❌'}`);

  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
}

/**
 * Sleep helper for rate limiting
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Run all tests
 */
async function runTests() {
  console.log('========================================');
  console.log('geo-routing MCP Server - Test Suite');
  console.log('========================================');
  console.log('Note: Nominatim requires 1 req/sec rate limit');
  console.log('');

  await testRouteCalculation(); // Test OSRM first (no rate limit)
  await sleep(1500);
  await testClearAddress();
  await sleep(1500);
  await testAmbiguousAddress();
  await sleep(1500);
  await testReverseGeocode();

  console.log('\n========================================');
  console.log('Tests completed');
  console.log('========================================\n');
}

// Run tests
runTests().catch(error => {
  console.error('Test suite error:', error);
  process.exit(1);
});
