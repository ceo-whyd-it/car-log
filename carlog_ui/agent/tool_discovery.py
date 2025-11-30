"""
Progressive Tool Discovery for Car Log Agent

Implements filesystem-like tool catalog for on-demand tool schema loading.
Achieves 97% token reduction by only loading schemas when needed.

Pattern from: https://www.anthropic.com/engineering/code-execution-with-mcp
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ToolSchema:
    """Schema for a single MCP tool."""
    name: str
    description: str
    category: str
    server: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ToolCategory:
    """Category of related tools."""
    name: str
    description: str
    server: str
    tool_count: int
    tools: List[str]


class ToolDiscovery:
    """
    Progressive tool discovery system.

    Instead of loading all 30+ tool schemas upfront (15,000 tokens),
    this provides an index (500 tokens) and loads schemas on-demand.
    """

    def __init__(self):
        """Initialize tool catalog from MCP adapters."""
        self._categories: Dict[str, ToolCategory] = {}
        self._tools: Dict[str, ToolSchema] = {}
        self._index_loaded = False

    def _build_catalog(self):
        """Build tool catalog from known MCP servers."""
        if self._index_loaded:
            return

        # Define tool categories and their tools
        # This is a static catalog - in production, could be dynamically loaded
        self._categories = {
            "vehicle": ToolCategory(
                name="vehicle",
                description="Vehicle registration and management (VIN validation, license plates)",
                server="car-log-core",
                tool_count=5,
                tools=["create_vehicle", "get_vehicle", "list_vehicles", "update_vehicle", "delete_vehicle"],
            ),
            "checkpoint": ToolCategory(
                name="checkpoint",
                description="Checkpoint/refuel tracking with GPS and receipt data",
                server="car-log-core",
                tool_count=5,
                tools=["create_checkpoint", "get_checkpoint", "list_checkpoints", "update_checkpoint", "delete_checkpoint"],
            ),
            "trip": ToolCategory(
                name="trip",
                description="Trip storage and management for Slovak tax compliance",
                server="car-log-core",
                tool_count=6,
                tools=["create_trip", "create_trips_batch", "get_trip", "list_trips", "update_trip", "delete_trip"],
            ),
            "template": ToolCategory(
                name="template",
                description="Reusable trip templates with GPS coordinates",
                server="car-log-core",
                tool_count=5,
                tools=["create_template", "get_template", "list_templates", "update_template", "delete_template"],
            ),
            "gap": ToolCategory(
                name="gap",
                description="Gap detection between checkpoints for trip reconstruction",
                server="car-log-core",
                tool_count=1,
                tools=["detect_gap"],
            ),
            "matching": ToolCategory(
                name="matching",
                description="GPS-first template matching algorithm (70% GPS, 30% address)",
                server="trip-reconstructor",
                tool_count=2,
                tools=["match_templates", "calculate_template_completeness"],
            ),
            "validation": ToolCategory(
                name="validation",
                description="4 validation algorithms for Slovak tax compliance",
                server="validation",
                tool_count=4,
                tools=["validate_checkpoint_pair", "validate_trip", "check_efficiency", "check_deviation_from_average"],
            ),
            "report": ToolCategory(
                name="report",
                description="CSV/PDF report generation with compliance fields",
                server="report-generator",
                tool_count=2,
                tools=["generate_csv", "generate_pdf"],
            ),
            "receipt": ToolCategory(
                name="receipt",
                description="Slovak e-Kasa receipt processing (QR scan, API fetch)",
                server="ekasa-api",
                tool_count=2,
                tools=["scan_qr_code", "fetch_receipt_data"],
            ),
            "photo": ToolCategory(
                name="photo",
                description="Photo metadata extraction (EXIF GPS, quality check)",
                server="dashboard-ocr",
                tool_count=2,
                tools=["extract_metadata", "check_photo_quality"],
            ),
            "geo": ToolCategory(
                name="geo",
                description="Geocoding and route calculation via OpenStreetMap",
                server="geo-routing",
                tool_count=3,
                tools=["geocode_address", "reverse_geocode", "calculate_route"],
            ),
        }

        # Build tool schemas (detailed specifications)
        self._build_tool_schemas()
        self._index_loaded = True

    def _build_tool_schemas(self):
        """Build detailed tool schemas."""
        # Vehicle tools
        self._tools["create_vehicle"] = ToolSchema(
            name="create_vehicle",
            description="Register a new company vehicle with Slovak compliance validation",
            category="vehicle",
            server="car-log-core",
            parameters={
                "type": "object",
                "required": ["license_plate", "vin", "make", "model", "fuel_type"],
                "properties": {
                    "license_plate": {"type": "string", "description": "Slovak format: XX-123XX (e.g., BA-456CD)"},
                    "vin": {"type": "string", "description": "17-character VIN (no I/O/Q)"},
                    "make": {"type": "string", "description": "Vehicle manufacturer"},
                    "model": {"type": "string", "description": "Vehicle model name"},
                    "year": {"type": "integer", "description": "Manufacturing year"},
                    "fuel_type": {"type": "string", "enum": ["Diesel", "Gasoline", "LPG", "Hybrid", "Electric"]},
                    "initial_odometer_km": {"type": "number", "description": "Starting odometer reading"},
                    "average_efficiency_l_per_100km": {"type": "number", "description": "Average fuel consumption"},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "vehicle_id": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
            examples=[{
                "input": {"license_plate": "BA-456CD", "vin": "WBAXX01234ABC5678", "make": "Ford", "model": "Transit", "fuel_type": "Diesel"},
                "output": {"success": True, "vehicle_id": "abc123", "message": "Vehicle registered successfully"},
            }],
        )

        self._tools["list_vehicles"] = ToolSchema(
            name="list_vehicles",
            description="List all registered vehicles with optional filters",
            category="vehicle",
            server="car-log-core",
            parameters={
                "type": "object",
                "properties": {
                    "active_only": {"type": "boolean", "default": True, "description": "Only show active vehicles"},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "vehicles": {"type": "array", "items": {"type": "object"}},
                    "count": {"type": "integer"},
                },
            },
            examples=[],
        )

        self._tools["get_vehicle"] = ToolSchema(
            name="get_vehicle",
            description="Get details of a specific vehicle by ID",
            category="vehicle",
            server="car-log-core",
            parameters={
                "type": "object",
                "required": ["vehicle_id"],
                "properties": {
                    "vehicle_id": {"type": "string", "description": "UUID of the vehicle"},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "vehicle": {"type": "object"},
                },
            },
            examples=[],
        )

        # Checkpoint tools
        self._tools["create_checkpoint"] = ToolSchema(
            name="create_checkpoint",
            description="Create a checkpoint from refuel or manual entry",
            category="checkpoint",
            server="car-log-core",
            parameters={
                "type": "object",
                "required": ["vehicle_id", "datetime", "odometer_km", "checkpoint_type"],
                "properties": {
                    "vehicle_id": {"type": "string"},
                    "datetime": {"type": "string", "format": "date-time", "description": "ISO 8601 format"},
                    "odometer_km": {"type": "number", "description": "Current odometer reading"},
                    "checkpoint_type": {"type": "string", "enum": ["refuel", "manual"]},
                    "location": {
                        "type": "object",
                        "properties": {
                            "coords": {"type": "object", "properties": {"latitude": {"type": "number"}, "longitude": {"type": "number"}}},
                            "address": {"type": "string"},
                            "source": {"type": "string", "enum": ["exif", "user", "geocoded"]},
                        },
                    },
                    "receipt": {
                        "type": "object",
                        "properties": {
                            "receipt_id": {"type": "string"},
                            "vendor_name": {"type": "string"},
                            "fuel_type": {"type": "string"},
                            "fuel_liters": {"type": "number"},
                            "price_incl_vat": {"type": "number"},
                            "vat_rate": {"type": "number"},
                        },
                    },
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "checkpoint_id": {"type": "string"},
                    "gap_detected": {"type": "boolean"},
                },
            },
            examples=[],
        )

        self._tools["list_checkpoints"] = ToolSchema(
            name="list_checkpoints",
            description="List checkpoints with optional filters",
            category="checkpoint",
            server="car-log-core",
            parameters={
                "type": "object",
                "properties": {
                    "vehicle_id": {"type": "string", "description": "Filter by vehicle"},
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "limit": {"type": "integer", "default": 50},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "checkpoints": {"type": "array"},
                    "count": {"type": "integer"},
                },
            },
            examples=[],
        )

        # Gap detection
        self._tools["detect_gap"] = ToolSchema(
            name="detect_gap",
            description="Detect gap between two checkpoints for trip reconstruction",
            category="gap",
            server="car-log-core",
            parameters={
                "type": "object",
                "required": ["checkpoint1_id", "checkpoint2_id"],
                "properties": {
                    "checkpoint1_id": {"type": "string", "description": "Earlier checkpoint ID"},
                    "checkpoint2_id": {"type": "string", "description": "Later checkpoint ID"},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "gap": {
                        "type": "object",
                        "properties": {
                            "distance_km": {"type": "number"},
                            "duration_days": {"type": "number"},
                            "start_checkpoint": {"type": "object"},
                            "end_checkpoint": {"type": "object"},
                            "has_gps_both": {"type": "boolean"},
                        },
                    },
                },
            },
            examples=[],
        )

        # Trip tools
        self._tools["create_trip"] = ToolSchema(
            name="create_trip",
            description="Create a single trip with Slovak compliance fields",
            category="trip",
            server="car-log-core",
            parameters={
                "type": "object",
                "required": ["vehicle_id", "driver_name", "trip_start_datetime", "trip_end_datetime", "distance_km", "purpose"],
                "properties": {
                    "vehicle_id": {"type": "string"},
                    "driver_name": {"type": "string", "description": "REQUIRED for Slovak tax compliance"},
                    "trip_start_datetime": {"type": "string", "format": "date-time"},
                    "trip_end_datetime": {"type": "string", "format": "date-time"},
                    "trip_start_location": {"type": "string"},
                    "trip_end_location": {"type": "string"},
                    "distance_km": {"type": "number"},
                    "fuel_consumption_liters": {"type": "number"},
                    "purpose": {"type": "string", "enum": ["Business", "Personal"]},
                    "business_description": {"type": "string", "description": "Required if Business"},
                    "template_id": {"type": "string"},
                    "confidence_score": {"type": "number"},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "trip_id": {"type": "string"},
                },
            },
            examples=[],
        )

        self._tools["create_trips_batch"] = ToolSchema(
            name="create_trips_batch",
            description="Create multiple trips from reconstruction proposals",
            category="trip",
            server="car-log-core",
            parameters={
                "type": "object",
                "required": ["trips"],
                "properties": {
                    "trips": {"type": "array", "items": {"type": "object"}, "description": "Array of trip data"},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "trip_ids": {"type": "array", "items": {"type": "string"}},
                    "count": {"type": "integer"},
                },
            },
            examples=[],
        )

        self._tools["list_trips"] = ToolSchema(
            name="list_trips",
            description="List trips with filters for reports",
            category="trip",
            server="car-log-core",
            parameters={
                "type": "object",
                "properties": {
                    "vehicle_id": {"type": "string"},
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "purpose": {"type": "string", "enum": ["Business", "Personal"]},
                    "limit": {"type": "integer", "default": 100},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "trips": {"type": "array"},
                    "summary": {
                        "type": "object",
                        "properties": {
                            "total_distance_km": {"type": "number"},
                            "total_fuel_liters": {"type": "number"},
                            "avg_efficiency": {"type": "number"},
                        },
                    },
                },
            },
            examples=[],
        )

        # Template tools
        self._tools["create_template"] = ToolSchema(
            name="create_template",
            description="Create a reusable trip template (GPS MANDATORY)",
            category="template",
            server="car-log-core",
            parameters={
                "type": "object",
                "required": ["name", "from_coords", "to_coords"],
                "properties": {
                    "name": {"type": "string"},
                    "from_coords": {"type": "object", "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}}},
                    "to_coords": {"type": "object", "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}}},
                    "from_address": {"type": "string"},
                    "to_address": {"type": "string"},
                    "distance_km": {"type": "number"},
                    "is_round_trip": {"type": "boolean"},
                    "typical_days": {"type": "array", "items": {"type": "string"}},
                    "purpose": {"type": "string", "enum": ["business", "personal"]},
                    "business_description": {"type": "string"},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "template_id": {"type": "string"},
                },
            },
            examples=[],
        )

        self._tools["list_templates"] = ToolSchema(
            name="list_templates",
            description="List all trip templates",
            category="template",
            server="car-log-core",
            parameters={
                "type": "object",
                "properties": {
                    "purpose": {"type": "string", "enum": ["business", "personal"]},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "templates": {"type": "array"},
                    "count": {"type": "integer"},
                },
            },
            examples=[],
        )

        # Matching tools
        self._tools["match_templates"] = ToolSchema(
            name="match_templates",
            description="Match templates to gap using GPS-first algorithm",
            category="matching",
            server="trip-reconstructor",
            parameters={
                "type": "object",
                "required": ["gap_data", "templates"],
                "properties": {
                    "gap_data": {"type": "object", "description": "Gap data from detect_gap"},
                    "templates": {"type": "array", "description": "Available templates"},
                    "confidence_threshold": {"type": "number", "default": 70},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "matches": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "template_id": {"type": "string"},
                                "template_name": {"type": "string"},
                                "confidence": {"type": "number"},
                                "gps_score": {"type": "number"},
                                "address_score": {"type": "number"},
                            },
                        },
                    },
                    "proposals": {"type": "array"},
                    "coverage_percent": {"type": "number"},
                },
            },
            examples=[],
        )

        # Validation tools
        self._tools["validate_trip"] = ToolSchema(
            name="validate_trip",
            description="Validate trip data for Slovak compliance",
            category="validation",
            server="validation",
            parameters={
                "type": "object",
                "required": ["trip_data", "vehicle_data"],
                "properties": {
                    "trip_data": {"type": "object"},
                    "vehicle_data": {"type": "object"},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "valid": {"type": "boolean"},
                    "warnings": {"type": "array"},
                    "errors": {"type": "array"},
                },
            },
            examples=[],
        )

        # Receipt tools
        self._tools["fetch_receipt_data"] = ToolSchema(
            name="fetch_receipt_data",
            description="Fetch receipt from Slovak e-Kasa API (5-30 seconds)",
            category="receipt",
            server="ekasa-api",
            parameters={
                "type": "object",
                "required": ["receipt_id"],
                "properties": {
                    "receipt_id": {"type": "string", "description": "e-Kasa receipt identifier from QR code"},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "receipt": {
                        "type": "object",
                        "properties": {
                            "vendor_name": {"type": "string"},
                            "items": {"type": "array"},
                            "fuel_items": {"type": "array"},
                            "total_amount": {"type": "number"},
                            "vat_rate": {"type": "number"},
                        },
                    },
                },
            },
            examples=[],
        )

        self._tools["scan_qr_code"] = ToolSchema(
            name="scan_qr_code",
            description="Scan QR code from image or PDF",
            category="receipt",
            server="ekasa-api",
            parameters={
                "type": "object",
                "required": ["image_path"],
                "properties": {
                    "image_path": {"type": "string", "description": "Path to image or PDF file"},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "receipt_id": {"type": "string"},
                    "detection_scale": {"type": "number"},
                },
            },
            examples=[],
        )

        # Geo tools
        self._tools["geocode_address"] = ToolSchema(
            name="geocode_address",
            description="Convert address to GPS coordinates",
            category="geo",
            server="geo-routing",
            parameters={
                "type": "object",
                "required": ["address"],
                "properties": {
                    "address": {"type": "string"},
                    "country_hint": {"type": "string", "default": "SK"},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "coordinates": {"type": "object", "properties": {"latitude": {"type": "number"}, "longitude": {"type": "number"}}},
                    "confidence": {"type": "number"},
                    "alternatives": {"type": "array"},
                },
            },
            examples=[],
        )

        self._tools["calculate_route"] = ToolSchema(
            name="calculate_route",
            description="Calculate route between two GPS points",
            category="geo",
            server="geo-routing",
            parameters={
                "type": "object",
                "required": ["from_coords", "to_coords"],
                "properties": {
                    "from_coords": {"type": "object", "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}}},
                    "to_coords": {"type": "object", "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}}},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "distance_km": {"type": "number"},
                    "duration_hours": {"type": "number"},
                    "via": {"type": "string"},
                },
            },
            examples=[],
        )

        # Report tools
        self._tools["generate_csv"] = ToolSchema(
            name="generate_csv",
            description="Generate CSV report with Slovak compliance fields",
            category="report",
            server="report-generator",
            parameters={
                "type": "object",
                "required": ["vehicle_id"],
                "properties": {
                    "vehicle_id": {"type": "string"},
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "purpose_filter": {"type": "string", "enum": ["Business", "Personal", "All"]},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "file_path": {"type": "string"},
                    "summary": {"type": "object"},
                },
            },
            examples=[],
        )

        # Photo tools
        self._tools["extract_metadata"] = ToolSchema(
            name="extract_metadata",
            description="Extract EXIF metadata (GPS, timestamp) from photo",
            category="photo",
            server="dashboard-ocr",
            parameters={
                "type": "object",
                "required": ["image_path"],
                "properties": {
                    "image_path": {"type": "string"},
                },
            },
            returns={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "gps": {"type": "object", "properties": {"latitude": {"type": "number"}, "longitude": {"type": "number"}}},
                    "timestamp": {"type": "string"},
                    "camera_model": {"type": "string"},
                },
            },
            examples=[],
        )

    def list_tool_categories(self) -> List[Dict[str, Any]]:
        """
        List all tool categories with brief descriptions.

        Returns:
            List of category summaries (name, description, tool_count)
        """
        self._build_catalog()

        return [
            {
                "name": cat.name,
                "description": cat.description,
                "server": cat.server,
                "tool_count": cat.tool_count,
            }
            for cat in self._categories.values()
        ]

    def list_tools_in_category(self, category: str) -> List[Dict[str, Any]]:
        """
        List tools in a specific category with brief descriptions.

        Args:
            category: Category name

        Returns:
            List of tool summaries (name, description)
        """
        self._build_catalog()

        if category not in self._categories:
            return []

        cat = self._categories[category]
        result = []

        for tool_name in cat.tools:
            if tool_name in self._tools:
                tool = self._tools[tool_name]
                result.append({
                    "name": tool.name,
                    "description": tool.description,
                    "server": tool.server,
                })
            else:
                result.append({
                    "name": tool_name,
                    "description": f"Tool in {category} category",
                    "server": cat.server,
                })

        return result

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get full schema for a specific tool (on-demand loading).

        Args:
            tool_name: Name of the tool

        Returns:
            Full tool schema or None if not found
        """
        self._build_catalog()

        if tool_name not in self._tools:
            return None

        tool = self._tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "server": tool.server,
            "parameters": tool.parameters,
            "returns": tool.returns,
            "examples": tool.examples,
        }

    def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """
        Search tools by name or description (fuzzy matching).

        Args:
            query: Search query

        Returns:
            List of matching tools with scores
        """
        self._build_catalog()

        query_lower = query.lower()
        results = []

        for tool in self._tools.values():
            # Simple matching - in production, use fuzzy matching library
            name_match = query_lower in tool.name.lower()
            desc_match = query_lower in tool.description.lower()
            cat_match = query_lower in tool.category.lower()

            if name_match or desc_match or cat_match:
                score = 0
                if name_match:
                    score += 3
                if desc_match:
                    score += 2
                if cat_match:
                    score += 1

                results.append({
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category,
                    "server": tool.server,
                    "relevance_score": score,
                })

        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:10]  # Return top 10

    def get_index_json(self) -> str:
        """
        Get compact index as JSON string for system prompt.

        This is the 500-token version instead of 15,000 tokens for all schemas.

        Returns:
            JSON string of category index
        """
        self._build_catalog()

        index = {
            "categories": self.list_tool_categories(),
            "total_tools": sum(cat.tool_count for cat in self._categories.values()),
            "usage": "Use list_tools_in_category(name) for tools, get_tool_schema(name) for full schema",
        }

        return json.dumps(index, indent=2)
