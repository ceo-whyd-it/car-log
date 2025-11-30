#!/usr/bin/env node

/**
 * geo-routing HTTP Server
 *
 * HTTP REST API wrapper for geo-routing MCP server.
 * Used by Gradio container to call geo-routing tools.
 *
 * Endpoints:
 * - GET /health - Health check
 * - GET /tools - List available tools
 * - POST /tools/geocode_address - Geocode address
 * - POST /tools/reverse_geocode - Reverse geocode
 * - POST /tools/calculate_route - Calculate route
 */

// OpenTelemetry instrumentation - must be first
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { HttpInstrumentation } from '@opentelemetry/instrumentation-http';
import { ExpressInstrumentation } from '@opentelemetry/instrumentation-express';
import { trace } from '@opentelemetry/api';
import winston from 'winston';

const sdk = new NodeSDK({
  serviceName: 'car-log-geo-routing',
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://mlflow:5050/v1/traces',
  }),
  instrumentations: [
    new HttpInstrumentation(),
    new ExpressInstrumentation(),
  ],
});

sdk.start();

// Winston logger with trace ID
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.printf(({ level, message, timestamp }) => {
      const span = trace.getActiveSpan();
      const traceId = span ? span.spanContext().traceId : 'no-trace';
      return `${timestamp} [${traceId}] ${level}: ${message}`;
    })
  ),
  transports: [new winston.transports.Console()],
});

logger.info('OpenTelemetry tracing initialized for geo-routing');

import express from 'express';
import cors from 'cors';
import axios from 'axios';
import NodeCache from 'node-cache';

// Environment configuration
const PORT = parseInt(process.env.PORT || '8002', 10);
const OSRM_BASE_URL = process.env.OSRM_BASE_URL || 'https://router.project-osrm.org';
const NOMINATIM_BASE_URL = process.env.NOMINATIM_BASE_URL || 'https://nominatim.openstreetmap.org';
const CACHE_TTL_HOURS = parseInt(process.env.CACHE_TTL_HOURS || '24', 10);

// Initialize cache (TTL in seconds)
const cache = new NodeCache({ stdTTL: CACHE_TTL_HOURS * 3600 });

// Axios instances
const nominatimClient = axios.create({
  baseURL: NOMINATIM_BASE_URL,
  headers: {
    'User-Agent': 'CarLog/1.0 (HTTP Server)',
  },
  timeout: 10000,
});

const osrmClient = axios.create({
  baseURL: OSRM_BASE_URL,
  timeout: 15000,
});

// Initialize Express
const app = express();
app.use(cors());
app.use(express.json());

/**
 * Calculate confidence score based on Nominatim result
 */
function calculateConfidence(result) {
  const importance = parseFloat(result.importance || 0);
  const typeScores = {
    'house': 1.0, 'street': 0.95, 'poi': 0.9, 'city': 0.7,
    'district': 0.6, 'region': 0.5, 'state': 0.4, 'country': 0.3,
  };
  const placeType = result.type || result.class || 'unknown';
  const typeScore = typeScores[placeType] || 0.5;
  return Math.round(Math.min(1.0, (importance + typeScore) / 2) * 100) / 100;
}

/**
 * Determine place type from Nominatim result
 */
function getPlaceType(result) {
  const addressType = result.addresstype || result.type || result.class;
  const typeMap = {
    'house': 'street', 'building': 'street', 'road': 'street',
    'city': 'city', 'town': 'city', 'village': 'city',
    'suburb': 'district', 'district': 'district',
    'administrative': 'region', 'state': 'region',
    'amenity': 'poi', 'shop': 'poi',
  };
  return typeMap[addressType] || 'city';
}

/**
 * Tool: geocode_address
 */
async function geocodeAddress(args) {
  const { address, country_hint } = args;

  if (!address || address.trim().length === 0) {
    return { success: false, error: 'Address is required' };
  }

  const cacheKey = `geocode:${address}:${country_hint || 'none'}`;
  const cached = cache.get(cacheKey);
  if (cached) return cached;

  try {
    const params = { q: address, format: 'json', addressdetails: 1, limit: 5 };
    if (country_hint) params.countrycodes = country_hint.toLowerCase();

    const response = await nominatimClient.get('/search', { params });
    if (!response.data || response.data.length === 0) {
      return { success: false, error: 'Address not found' };
    }

    const results = response.data.map(r => ({
      address: r.display_name,
      coordinates: { lat: parseFloat(r.lat), lng: parseFloat(r.lon) },
      confidence: calculateConfidence(r),
      type: getPlaceType(r),
    }));
    results.sort((a, b) => b.confidence - a.confidence);

    const topResult = results[0];
    const result = {
      success: true,
      coordinates: { latitude: topResult.coordinates.lat, longitude: topResult.coordinates.lng },
      normalized_address: topResult.address,
      confidence: topResult.confidence,
      alternatives: [],
    };

    if (topResult.confidence < 0.7 && results.length > 1) {
      result.alternatives = results.slice(0, 3).map(r => ({
        address: r.address, coordinates: r.coordinates, confidence: r.confidence, type: r.type,
      }));
    }

    cache.set(cacheKey, result);
    return result;
  } catch (error) {
    return { success: false, error: `Geocoding failed: ${error.message}` };
  }
}

/**
 * Tool: reverse_geocode
 */
async function reverseGeocode(args) {
  const { latitude, longitude } = args;

  if (typeof latitude !== 'number' || typeof longitude !== 'number') {
    return { success: false, error: 'Invalid coordinates' };
  }
  if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
    return { success: false, error: 'Coordinates out of range' };
  }

  const cacheKey = `reverse:${latitude.toFixed(6)},${longitude.toFixed(6)}`;
  const cached = cache.get(cacheKey);
  if (cached) return cached;

  try {
    const response = await nominatimClient.get('/reverse', {
      params: { lat: latitude, lon: longitude, format: 'json', addressdetails: 1 },
    });

    if (!response.data) {
      return { success: false, error: 'No address found for coordinates' };
    }

    const data = response.data;
    const addr = data.address || {};
    const result = {
      success: true,
      address: {
        street: addr.road || '',
        house_number: addr.house_number || '',
        city: addr.city || addr.town || addr.village || '',
        postal_code: addr.postcode || '',
        country: addr.country || '',
        formatted: data.display_name || '',
      },
    };

    if (data.name && (data.class === 'amenity' || data.class === 'shop')) {
      result.poi = data.name;
    }

    cache.set(cacheKey, result);
    return result;
  } catch (error) {
    return { success: false, error: `Reverse geocoding failed: ${error.message}` };
  }
}

/**
 * Tool: calculate_route
 */
async function calculateRoute(args) {
  const { from_coords, to_coords, alternatives = 1, vehicle = 'car' } = args;

  if (!from_coords || !to_coords) {
    return { success: false, error: 'from_coords and to_coords are required' };
  }

  const { lat: fromLat, lng: fromLng } = from_coords;
  const { lat: toLat, lng: toLng } = to_coords;

  if (typeof fromLat !== 'number' || typeof fromLng !== 'number' ||
      typeof toLat !== 'number' || typeof toLng !== 'number') {
    return { success: false, error: 'Invalid coordinates' };
  }

  const cacheKey = `route:${fromLat},${fromLng}:${toLat},${toLng}:${alternatives}:${vehicle}`;
  const cached = cache.get(cacheKey);
  if (cached) return cached;

  try {
    const coords = `${fromLng},${fromLat};${toLng},${toLat}`;
    const response = await osrmClient.get(`/route/v1/${vehicle}/${coords}`, {
      params: { overview: 'full', alternatives: alternatives > 1 ? 'true' : 'false', steps: 'true' },
    });

    if (!response.data || response.data.code !== 'Ok') {
      return { success: false, error: 'Route calculation failed' };
    }

    const routes = response.data.routes.map(route => {
      const highways = new Set();
      if (route.legs?.[0]?.steps) {
        route.legs[0].steps.forEach(step => {
          if (step.name?.match(/^(D\d+|E\d+|R\d+|I\/\d+)/)) {
            highways.add(step.name);
          }
        });
      }

      const highwayList = Array.from(highways);
      let routeType = 'local';
      if (highwayList.some(h => h.startsWith('D') || h.startsWith('E'))) {
        routeType = 'highway';
      } else if (highwayList.length > 0) {
        routeType = 'mixed';
      }

      return {
        distance_km: Math.round(route.distance / 10) / 100,
        duration_hours: Math.round(route.duration / 36) / 100,
        via: highwayList.length > 0 ? `via ${highwayList.join(', ')}` : 'local roads',
        route_type: routeType,
      };
    });

    const result = { success: true, routes };
    cache.set(cacheKey, result);
    return result;
  } catch (error) {
    return { success: false, error: `Route calculation failed: ${error.message}` };
  }
}

// Tool definitions for /tools endpoint
const TOOLS = [
  {
    name: 'geocode_address',
    description: 'Convert address text to GPS coordinates with ambiguity handling',
    inputSchema: {
      type: 'object',
      properties: {
        address: { type: 'string', description: 'Address to geocode' },
        country_hint: { type: 'string', description: 'ISO country code (e.g., SK)' },
      },
      required: ['address'],
    },
  },
  {
    name: 'reverse_geocode',
    description: 'Convert GPS coordinates to human-readable address',
    inputSchema: {
      type: 'object',
      properties: {
        latitude: { type: 'number', description: 'Latitude' },
        longitude: { type: 'number', description: 'Longitude' },
      },
      required: ['latitude', 'longitude'],
    },
  },
  {
    name: 'calculate_route',
    description: 'Calculate route between two GPS coordinates using OSRM',
    inputSchema: {
      type: 'object',
      properties: {
        from_coords: { type: 'object', properties: { lat: { type: 'number' }, lng: { type: 'number' } }, required: ['lat', 'lng'] },
        to_coords: { type: 'object', properties: { lat: { type: 'number' }, lng: { type: 'number' } }, required: ['lat', 'lng'] },
        alternatives: { type: 'integer', minimum: 1, maximum: 3, default: 1 },
        vehicle: { type: 'string', enum: ['car', 'truck'], default: 'car' },
      },
      required: ['from_coords', 'to_coords'],
    },
  },
];

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.get('/tools', (req, res) => {
  res.json({ tools: TOOLS });
});

app.post('/tools/geocode_address', async (req, res) => {
  const result = await geocodeAddress(req.body);
  res.json(result);
});

app.post('/tools/reverse_geocode', async (req, res) => {
  const result = await reverseGeocode(req.body);
  res.json(result);
});

app.post('/tools/calculate_route', async (req, res) => {
  const result = await calculateRoute(req.body);
  res.json(result);
});

// Generic tool endpoint (for compatibility)
app.post('/tools/:toolName', async (req, res) => {
  const { toolName } = req.params;
  let result;

  switch (toolName) {
    case 'geocode_address':
      result = await geocodeAddress(req.body);
      break;
    case 'reverse_geocode':
      result = await reverseGeocode(req.body);
      break;
    case 'calculate_route':
      result = await calculateRoute(req.body);
      break;
    default:
      result = { success: false, error: `Unknown tool: ${toolName}` };
  }

  res.json(result);
});

// Start server
app.listen(PORT, () => {
  logger.info(`geo-routing HTTP server running on port ${PORT}`);
  logger.info(`Cache TTL: ${CACHE_TTL_HOURS} hours`);
  logger.info(`OSRM: ${OSRM_BASE_URL}`);
  logger.info(`Nominatim: ${NOMINATIM_BASE_URL}`);
});
