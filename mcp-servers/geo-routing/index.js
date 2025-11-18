#!/usr/bin/env node

/**
 * geo-routing MCP Server
 *
 * Provides geocoding and route calculation via OpenStreetMap (Nominatim + OSRM).
 *
 * Tools:
 * - geocode_address: Convert address to GPS coordinates with ambiguity handling
 * - reverse_geocode: Convert GPS coordinates to human-readable address
 * - calculate_route: Calculate route between two points
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
import NodeCache from 'node-cache';

// Environment configuration
const OSRM_BASE_URL = process.env.OSRM_BASE_URL || 'https://router.project-osrm.org';
const NOMINATIM_BASE_URL = process.env.NOMINATIM_BASE_URL || 'https://nominatim.openstreetmap.org';
const CACHE_TTL_HOURS = parseInt(process.env.CACHE_TTL_HOURS || '24', 10);

// Initialize cache (TTL in seconds)
const cache = new NodeCache({ stdTTL: CACHE_TTL_HOURS * 3600 });

// Axios instance with proper headers (required by Nominatim)
const nominatimClient = axios.create({
  baseURL: NOMINATIM_BASE_URL,
  headers: {
    'User-Agent': 'CarLog/1.0 (MCP Server)',
  },
  timeout: 10000,
});

const osrmClient = axios.create({
  baseURL: OSRM_BASE_URL,
  timeout: 15000,
});

/**
 * Normalize address for better matching
 */
function normalizeAddress(address) {
  return address
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Remove diacritics
    .trim();
}

/**
 * Calculate confidence score based on Nominatim result
 */
function calculateConfidence(result) {
  // Nominatim doesn't provide confidence directly, so we infer from:
  // 1. Place importance (0-1)
  // 2. Address type specificity
  // 3. Bounding box size

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

  // Get type score
  const placeType = result.type || result.class || 'unknown';
  let typeScore = typeScores[placeType] || 0.5;

  // Combine importance and type
  const confidence = Math.min(1.0, (importance + typeScore) / 2);

  return Math.round(confidence * 100) / 100;
}

/**
 * Determine place type from Nominatim result
 */
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
 * Tool: geocode_address
 * Convert address text to GPS coordinates with ambiguity handling
 */
async function geocodeAddress(args) {
  const { address, country_hint } = args;

  if (!address || address.trim().length === 0) {
    return {
      success: false,
      error: 'Address is required',
    };
  }

  // Check cache
  const cacheKey = `geocode:${address}:${country_hint || 'none'}`;
  const cached = cache.get(cacheKey);
  if (cached) {
    return cached;
  }

  try {
    // Build query parameters
    const params = {
      q: address,
      format: 'json',
      addressdetails: 1,
      limit: 5, // Get multiple results to check for ambiguity
    };

    if (country_hint) {
      params.countrycodes = country_hint.toLowerCase();
    }

    // Call Nominatim API
    const response = await nominatimClient.get('/search', { params });

    if (!response.data || response.data.length === 0) {
      return {
        success: false,
        error: 'Address not found',
      };
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
      raw: r,
    }));

    // Sort by confidence
    results.sort((a, b) => b.confidence - a.confidence);

    const topResult = results[0];

    // Build response
    const result = {
      success: true,
      coordinates: {
        latitude: topResult.coordinates.lat,
        longitude: topResult.coordinates.lng,
      },
      normalized_address: topResult.address,
      confidence: topResult.confidence,
      alternatives: [],
    };

    // If confidence < 0.7, include alternatives
    if (topResult.confidence < 0.7 && results.length > 1) {
      result.alternatives = results.slice(0, 3).map(r => ({
        address: r.address,
        coordinates: r.coordinates,
        confidence: r.confidence,
        type: r.type,
      }));
    }

    // Cache result
    cache.set(cacheKey, result);

    return result;

  } catch (error) {
    console.error('Geocoding error:', error.message);
    return {
      success: false,
      error: `Geocoding failed: ${error.message}`,
    };
  }
}

/**
 * Tool: reverse_geocode
 * Convert GPS coordinates to human-readable address
 */
async function reverseGeocode(args) {
  const { latitude, longitude } = args;

  if (typeof latitude !== 'number' || typeof longitude !== 'number') {
    return {
      error: 'Invalid coordinates',
    };
  }

  if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
    return {
      error: 'Coordinates out of range',
    };
  }

  // Check cache
  const cacheKey = `reverse:${latitude.toFixed(6)},${longitude.toFixed(6)}`;
  const cached = cache.get(cacheKey);
  if (cached) {
    return cached;
  }

  try {
    // Call Nominatim reverse geocoding
    const response = await nominatimClient.get('/reverse', {
      params: {
        lat: latitude,
        lon: longitude,
        format: 'json',
        addressdetails: 1,
      },
    });

    if (!response.data) {
      return {
        error: 'No address found for coordinates',
      };
    }

    const data = response.data;
    const addr = data.address || {};

    // Build structured address
    const result = {
      address: {
        street: addr.road || '',
        house_number: addr.house_number || '',
        city: addr.city || addr.town || addr.village || '',
        postal_code: addr.postcode || '',
        country: addr.country || '',
        formatted: data.display_name || '',
      },
    };

    // Check for POI (amenity, shop, etc.)
    if (data.name && (data.class === 'amenity' || data.class === 'shop')) {
      result.poi = data.name;
    }

    // Cache result
    cache.set(cacheKey, result);

    return result;

  } catch (error) {
    console.error('Reverse geocoding error:', error.message);
    return {
      error: `Reverse geocoding failed: ${error.message}`,
    };
  }
}

/**
 * Tool: calculate_route
 * Calculate route between two GPS coordinates using OSRM
 */
async function calculateRoute(args) {
  const { from_coords, to_coords, alternatives = 1, vehicle = 'car' } = args;

  if (!from_coords || !to_coords) {
    return {
      error: 'from_coords and to_coords are required',
    };
  }

  const { lat: fromLat, lng: fromLng } = from_coords;
  const { lat: toLat, lng: toLng } = to_coords;

  if (typeof fromLat !== 'number' || typeof fromLng !== 'number' ||
      typeof toLat !== 'number' || typeof toLng !== 'number') {
    return {
      error: 'Invalid coordinates',
    };
  }

  // Check cache
  const cacheKey = `route:${fromLat},${fromLng}:${toLat},${toLng}:${alternatives}:${vehicle}`;
  const cached = cache.get(cacheKey);
  if (cached) {
    return cached;
  }

  try {
    // OSRM expects lon,lat (not lat,lon!)
    const coords = `${fromLng},${fromLat};${toLng},${toLat}`;

    // Call OSRM route API
    const response = await osrmClient.get(`/route/v1/${vehicle}/${coords}`, {
      params: {
        overview: 'full',
        alternatives: alternatives > 1 ? 'true' : 'false',
        steps: 'true',
        annotations: 'false',
      },
    });

    if (!response.data || response.data.code !== 'Ok') {
      return {
        error: 'Route calculation failed',
      };
    }

    const routes = response.data.routes.map(route => {
      // Extract highway names from steps
      const highways = new Set();
      if (route.legs && route.legs[0] && route.legs[0].steps) {
        route.legs[0].steps.forEach(step => {
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

      // Build via string
      const via = highwayList.length > 0
        ? `via ${highwayList.join(', ')}`
        : 'local roads';

      return {
        distance_km: Math.round(route.distance / 10) / 100, // meters to km, 2 decimals
        duration_hours: Math.round(route.duration / 36) / 100, // seconds to hours, 2 decimals
        via,
        route_type: routeType,
        waypoints: route.legs && route.legs[0] && route.legs[0].steps
          ? route.legs[0].steps
              .filter(s => s.name && s.name.length > 0)
              .slice(0, 5)
              .map(s => ({
                name: s.name,
                latitude: s.maneuver ? s.maneuver.location[1] : 0,
                longitude: s.maneuver ? s.maneuver.location[0] : 0,
              }))
          : [],
      };
    });

    const result = { routes };

    // Cache result
    cache.set(cacheKey, result);

    return result;

  } catch (error) {
    console.error('Route calculation error:', error.message);
    return {
      error: `Route calculation failed: ${error.message}`,
    };
  }
}

/**
 * Initialize MCP server
 */
const server = new Server(
  {
    name: 'geo-routing',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

/**
 * List available tools
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'geocode_address',
        description: 'Convert address text to GPS coordinates with ambiguity handling. Returns alternatives when confidence < 0.7.',
        inputSchema: {
          type: 'object',
          properties: {
            address: {
              type: 'string',
              description: 'Address to geocode (e.g., "Hlavná 45, Bratislava" or "Košice")',
            },
            country_hint: {
              type: 'string',
              description: 'ISO country code (e.g., SK, CZ, DE) - improves accuracy',
            },
          },
          required: ['address'],
        },
      },
      {
        name: 'reverse_geocode',
        description: 'Convert GPS coordinates to human-readable address. Returns structured address with POI if available.',
        inputSchema: {
          type: 'object',
          properties: {
            latitude: {
              type: 'number',
              description: 'Latitude (-90 to 90)',
              minimum: -90,
              maximum: 90,
            },
            longitude: {
              type: 'number',
              description: 'Longitude (-180 to 180)',
              minimum: -180,
              maximum: 180,
            },
          },
          required: ['latitude', 'longitude'],
        },
      },
      {
        name: 'calculate_route',
        description: 'Calculate route between two GPS coordinates using OSRM. Returns distance, duration, and route summary.',
        inputSchema: {
          type: 'object',
          properties: {
            from_coords: {
              type: 'object',
              properties: {
                lat: { type: 'number', description: 'Start latitude' },
                lng: { type: 'number', description: 'Start longitude' },
              },
              required: ['lat', 'lng'],
            },
            to_coords: {
              type: 'object',
              properties: {
                lat: { type: 'number', description: 'End latitude' },
                lng: { type: 'number', description: 'End longitude' },
              },
              required: ['lat', 'lng'],
            },
            alternatives: {
              type: 'integer',
              description: 'Number of alternative routes (1-3)',
              minimum: 1,
              maximum: 3,
              default: 1,
            },
            vehicle: {
              type: 'string',
              description: 'Vehicle type',
              enum: ['car', 'truck'],
              default: 'car',
            },
          },
          required: ['from_coords', 'to_coords'],
        },
      },
    ],
  };
});

/**
 * Handle tool calls
 */
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result;

    switch (name) {
      case 'geocode_address':
        result = await geocodeAddress(args);
        break;

      case 'reverse_geocode':
        result = await reverseGeocode(args);
        break;

      case 'calculate_route':
        result = await calculateRoute(args);
        break;

      default:
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({ error: `Unknown tool: ${name}` }),
            },
          ],
        };
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };

  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            error: `Tool execution failed: ${error.message}`,
          }),
        },
      ],
      isError: true,
    };
  }
});

/**
 * Start server
 */
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('geo-routing MCP server running on stdio');
  console.error(`Cache TTL: ${CACHE_TTL_HOURS} hours`);
  console.error(`OSRM: ${OSRM_BASE_URL}`);
  console.error(`Nominatim: ${NOMINATIM_BASE_URL}`);
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
