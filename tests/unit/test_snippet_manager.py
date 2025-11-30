"""
Unit tests for SnippetManager.

Run with: pytest tests/unit/test_snippet_manager.py -v
"""
import pytest
import sys
sys.path.insert(0, ".")

from carlog_ui.agent.snippet_manager import SnippetManager, SnippetHeader


class TestSnippetHeaderDataclass:
    """Test SnippetHeader dataclass."""

    def test_create_minimal_header(self):
        """Create header with required fields only."""
        header = SnippetHeader(
            snippet="test_snippet",
            mcp="car_log_core",
            description="Test description",
            triggers=["test", "demo"]
        )
        assert header.snippet == "test_snippet"
        assert header.mcp == "car_log_core"
        assert header.description == "Test description"
        assert header.triggers == ["test", "demo"]
        assert header.skill is None
        assert header.params is None
        assert header.returns is None
        assert header.version == "1.0"

    def test_create_full_header(self):
        """Create header with all fields."""
        header = SnippetHeader(
            snippet="full_snippet",
            mcp="geo_routing",
            description="Full test",
            triggers=["full", "complete"],
            skill="routing",
            params="address: str",
            returns="coordinates dict",
            version="2.0"
        )
        assert header.skill == "routing"
        assert header.params == "address: str"
        assert header.returns == "coordinates dict"
        assert header.version == "2.0"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        header = SnippetHeader(
            snippet="dict_test",
            mcp="validation",
            description="Dict test",
            triggers=["dict"]
        )
        d = header.to_dict()
        assert d["snippet"] == "dict_test"
        assert d["mcp"] == "validation"
        assert d["triggers"] == ["dict"]
        assert d["skill"] is None


class TestParseHeader:
    """Test header parsing from code."""

    def setup_method(self):
        self.manager = SnippetManager()

    def test_parse_valid_header(self):
        """Parse valid snippet header."""
        code = '''"""
@snippet: list_vehicles
@mcp: car_log_core
@description: List all vehicles in the system
@triggers: list vehicles, show vehicles, get vehicles
@version: 1.0
"""
async def run():
    return await car_log_core.list_vehicles({})
'''
        header = self.manager.parse_header(code)
        assert header is not None
        assert header.snippet == "list_vehicles"
        assert header.mcp == "car_log_core"
        assert header.description == "List all vehicles in the system"
        assert header.triggers == ["list vehicles", "show vehicles", "get vehicles"]
        assert header.version == "1.0"

    def test_parse_header_with_all_fields(self):
        """Parse header with optional fields."""
        code = '''"""
@snippet: create_vehicle
@mcp: car_log_core
@skill: vehicle_setup
@description: Create a new vehicle
@triggers: create vehicle, add vehicle, new car
@params: name, make, model, year, vin, license_plate
@returns: vehicle_id
@version: 1.2
"""
async def run(name, make, model):
    pass
'''
        header = self.manager.parse_header(code)
        assert header is not None
        assert header.skill == "vehicle_setup"
        assert header.params == "name, make, model, year, vin, license_plate"
        assert header.returns == "vehicle_id"
        assert header.version == "1.2"

    def test_parse_header_missing_required_field(self):
        """Return None if required field missing."""
        code = '''"""
@snippet: incomplete
@mcp: car_log_core
@description: Missing triggers
"""
async def run():
    pass
'''
        header = self.manager.parse_header(code)
        assert header is None

    def test_parse_no_docstring(self):
        """Return None if no docstring."""
        code = '''
async def run():
    return await car_log_core.list_vehicles({})
'''
        header = self.manager.parse_header(code)
        assert header is None

    def test_parse_single_quote_docstring(self):
        """Parse single-quote docstring."""
        code = """'''
@snippet: single_quote
@mcp: geo_routing
@description: Test single quotes
@triggers: test
'''
async def run():
    pass
"""
        header = self.manager.parse_header(code)
        assert header is not None
        assert header.snippet == "single_quote"

    def test_parse_default_version(self):
        """Use default version 1.0 if not specified."""
        code = '''"""
@snippet: no_version
@mcp: validation
@description: No version specified
@triggers: test
"""
async def run():
    pass
'''
        header = self.manager.parse_header(code)
        assert header is not None
        assert header.version == "1.0"


class TestGenerateHeader:
    """Test header generation."""

    def setup_method(self):
        self.manager = SnippetManager()

    def test_generate_minimal_header(self):
        """Generate header with required fields."""
        header = self.manager.generate_header(
            snippet="test_gen",
            mcp="car_log_core",
            description="Generated test",
            triggers=["test", "gen"]
        )
        assert '@snippet: test_gen' in header
        assert '@mcp: car_log_core' in header
        assert '@description: Generated test' in header
        assert '@triggers: test, gen' in header
        assert '@version: 1.0' in header
        assert header.startswith('"""')
        assert header.endswith('"""')

    def test_generate_full_header(self):
        """Generate header with all fields."""
        header = self.manager.generate_header(
            snippet="full_gen",
            mcp="geo_routing",
            description="Full generation",
            triggers=["full"],
            skill="geocoding",
            params="address: str",
            returns="coords: dict",
            version="2.0"
        )
        assert '@skill: geocoding' in header
        assert '@params: address: str' in header
        assert '@returns: coords: dict' in header
        assert '@version: 2.0' in header

    def test_generate_header_too_long(self):
        """Raise error if header exceeds limit."""
        with pytest.raises(ValueError) as exc_info:
            self.manager.generate_header(
                snippet="x" * 100,
                mcp="car_log_core",
                description="y" * 500,
                triggers=["z" * 100]
            )
        assert "exceeds" in str(exc_info.value)

    def test_roundtrip_parse_generate(self):
        """Generated header can be parsed back."""
        header_str = self.manager.generate_header(
            snippet="roundtrip",
            mcp="validation",
            description="Test roundtrip",
            triggers=["round", "trip"],
            skill="testing"
        )
        # Add some code after header
        full_code = header_str + "\nasync def run(): pass"
        parsed = self.manager.parse_header(full_code)
        assert parsed is not None
        assert parsed.snippet == "roundtrip"
        assert parsed.mcp == "validation"
        assert parsed.skill == "testing"
        assert parsed.triggers == ["round", "trip"]


class TestValidateHeader:
    """Test header validation."""

    def setup_method(self):
        self.manager = SnippetManager()

    def test_valid_header(self):
        """Valid header passes validation."""
        header = SnippetHeader(
            snippet="valid_snippet",
            mcp="car_log_core",
            description="Valid description",
            triggers=["test"]
        )
        is_valid, errors = self.manager.validate_header(header)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_mcp(self):
        """Invalid MCP name fails validation."""
        header = SnippetHeader(
            snippet="test",
            mcp="invalid_mcp",
            description="Test",
            triggers=["test"]
        )
        is_valid, errors = self.manager.validate_header(header)
        assert is_valid is False
        assert any("Invalid MCP" in e for e in errors)

    def test_empty_snippet_name(self):
        """Empty snippet name fails validation."""
        header = SnippetHeader(
            snippet="",
            mcp="car_log_core",
            description="Test",
            triggers=["test"]
        )
        is_valid, errors = self.manager.validate_header(header)
        assert is_valid is False
        assert any("@snippet" in e for e in errors)

    def test_invalid_snippet_name_chars(self):
        """Snippet name with invalid chars fails validation."""
        header = SnippetHeader(
            snippet="test-snippet",  # hyphen not allowed
            mcp="car_log_core",
            description="Test",
            triggers=["test"]
        )
        is_valid, errors = self.manager.validate_header(header)
        assert is_valid is False
        assert any("alphanumeric" in e for e in errors)

    def test_underscore_in_snippet_name(self):
        """Snippet name with underscores is valid."""
        header = SnippetHeader(
            snippet="test_snippet_name",
            mcp="geo_routing",
            description="Test",
            triggers=["test"]
        )
        is_valid, errors = self.manager.validate_header(header)
        assert is_valid is True

    def test_empty_triggers(self):
        """Empty triggers list fails validation."""
        header = SnippetHeader(
            snippet="test",
            mcp="car_log_core",
            description="Test",
            triggers=[]
        )
        is_valid, errors = self.manager.validate_header(header)
        assert is_valid is False
        assert any("@triggers" in e for e in errors)

    def test_all_valid_mcps(self):
        """All predefined MCP names are valid."""
        valid_mcps = [
            'car_log_core', 'geo_routing', 'validation',
            'trip_reconstructor', 'ekasa_api', 'dashboard_ocr',
            'report_generator'
        ]
        for mcp in valid_mcps:
            header = SnippetHeader(
                snippet="test",
                mcp=mcp,
                description="Test",
                triggers=["test"]
            )
            is_valid, errors = self.manager.validate_header(header)
            assert is_valid is True, f"MCP {mcp} should be valid"


class TestShouldStore:
    """Test should_store decision logic."""

    def setup_method(self):
        self.manager = SnippetManager()

    def test_failed_execution_not_stored(self):
        """Failed code should not be stored."""
        code = "await car_log_core.list_vehicles({})"
        result = self.manager.should_store(code, success=False, stdout="error")
        assert result is False

    def test_trivial_code_not_stored(self):
        """Code with < 5 lines should not be stored."""
        code = """x = 1
y = 2
z = await car_log_core.list_vehicles({})"""
        result = self.manager.should_store(code, success=True, stdout="ok")
        assert result is False

    def test_no_mcp_call_not_stored(self):
        """Code without MCP calls should not be stored."""
        code = """
line1 = 1
line2 = 2
line3 = 3
line4 = 4
line5 = 5
result = some_function()
"""
        result = self.manager.should_store(code, success=True, stdout="ok")
        assert result is False

    def test_complex_workflow_stored(self):
        """Multi-step MCP workflow should be stored."""
        code = """
# Step 1
vehicles = await car_log_core.list_vehicles({})

# Step 2
for v in vehicles:
    checkpoints = await car_log_core.list_checkpoints({'vehicle_id': v['id']})

# Step 3
result = await validation.validate_trip({})
"""
        result = self.manager.should_store(code, success=True, stdout="processed")
        assert result is True

    def test_single_mcp_with_output_stored(self):
        """Single MCP call with useful output should be stored."""
        code = """
# Get vehicles
adapter = CarLogCoreAdapter()
result = await car_log_core.list_vehicles({})
for v in result:
    print(v['name'])
"""
        result = self.manager.should_store(code, success=True, stdout="Vehicle 1\nVehicle 2")
        assert result is True

    def test_error_in_output_not_stored(self):
        """Code with 'error' in output should not be stored."""
        code = """
# Test code
result = await car_log_core.list_vehicles({})
await car_log_core.get_vehicle({})
check = await car_log_core.list_checkpoints({})
"""
        result = self.manager.should_store(code, success=True, stdout="Error: something failed")
        assert result is False


class TestExtractCodeBody:
    """Test code body extraction."""

    def setup_method(self):
        self.manager = SnippetManager()

    def test_extract_body_double_quotes(self):
        """Extract body after double-quote docstring."""
        code = '''"""
@snippet: test
@mcp: car_log_core
@description: Test
@triggers: test
"""
async def run():
    return await car_log_core.list_vehicles({})
'''
        body = self.manager.extract_code_body(code)
        assert 'async def run():' in body
        assert '@snippet' not in body
        assert '"""' not in body

    def test_extract_body_single_quotes(self):
        """Extract body after single-quote docstring."""
        code = """'''
@snippet: test
@mcp: car_log_core
@description: Test
@triggers: test
'''
async def run():
    pass
"""
        body = self.manager.extract_code_body(code)
        assert 'async def run():' in body
        assert '@snippet' not in body

    def test_extract_body_single_line_docstring(self):
        """Extract body after single-line docstring."""
        code = '''"""@snippet: test"""
async def run():
    pass
'''
        body = self.manager.extract_code_body(code)
        assert 'async def run():' in body

    def test_extract_body_no_docstring(self):
        """Return full code if no docstring."""
        code = '''async def run():
    return await car_log_core.list_vehicles({})
'''
        body = self.manager.extract_code_body(code)
        assert 'async def run():' in body


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
