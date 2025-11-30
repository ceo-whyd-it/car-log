"""
Unit tests for CodeLibrary.

Run with: pytest tests/unit/test_code_library.py -v
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import sys
sys.path.insert(0, ".")

from carlog_ui.agent.code_library import CodeLibrary, SnippetEntry, MatchResult


class TestCodeLibraryScan:
    """Test library scanning."""

    def setup_method(self):
        """Create temporary library directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.library = CodeLibrary(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scan_empty_directory(self):
        """Scan empty directory returns 0."""
        count = self.library.scan()
        assert count == 0

    def test_scan_nonexistent_directory(self):
        """Scan nonexistent directory returns 0."""
        library = CodeLibrary("/nonexistent/path")
        count = library.scan()
        assert count == 0

    def test_scan_valid_snippet(self):
        """Scan finds valid snippet."""
        snippet_dir = Path(self.temp_dir) / "car_log_core"
        snippet_dir.mkdir(parents=True)

        code = '''"""
@snippet: list_vehicles
@mcp: car_log_core
@description: List all vehicles
@triggers: list vehicles, show vehicles
"""
async def run():
    return await car_log_core.list_vehicles({})
'''
        (snippet_dir / "list_vehicles.py").write_text(code)

        count = self.library.scan()
        assert count == 1

        snippet = self.library.get_snippet("list_vehicles")
        assert snippet is not None
        assert snippet.mcp == "car_log_core"
        assert snippet.description == "List all vehicles"

    def test_scan_skips_invalid_header(self):
        """Scan skips files with invalid headers."""
        snippet_dir = Path(self.temp_dir) / "car_log_core"
        snippet_dir.mkdir(parents=True)

        # Missing required @triggers field
        code = '''"""
@snippet: incomplete
@mcp: car_log_core
@description: Incomplete header
"""
async def run():
    pass
'''
        (snippet_dir / "incomplete.py").write_text(code)

        count = self.library.scan()
        assert count == 0

    def test_scan_skips_init_files(self):
        """Scan skips __init__.py files."""
        snippet_dir = Path(self.temp_dir) / "car_log_core"
        snippet_dir.mkdir(parents=True)

        (snippet_dir / "__init__.py").write_text("# init")

        count = self.library.scan()
        assert count == 0

    def test_scan_multiple_snippets(self):
        """Scan finds multiple valid snippets."""
        snippet_dir = Path(self.temp_dir) / "car_log_core"
        snippet_dir.mkdir(parents=True)

        # Snippet 1
        code1 = '''"""
@snippet: list_vehicles
@mcp: car_log_core
@description: List vehicles
@triggers: list, show
"""
async def run(): pass
'''
        (snippet_dir / "list_vehicles.py").write_text(code1)

        # Snippet 2
        code2 = '''"""
@snippet: create_vehicle
@mcp: car_log_core
@description: Create vehicle
@triggers: create, add
"""
async def run(): pass
'''
        (snippet_dir / "create_vehicle.py").write_text(code2)

        count = self.library.scan()
        assert count == 2


class TestCodeLibraryMatch:
    """Test snippet matching."""

    def setup_method(self):
        """Create library with test snippets."""
        self.temp_dir = tempfile.mkdtemp()
        self.library = CodeLibrary(self.temp_dir)

        # Create test snippets
        snippet_dir = Path(self.temp_dir) / "car_log_core"
        snippet_dir.mkdir(parents=True)

        snippets = [
            ("list_vehicles", "List all vehicles", "list vehicles, show cars, get vehicles"),
            ("create_vehicle", "Create a new vehicle", "create vehicle, add car, new vehicle"),
            ("delete_vehicle", "Delete a vehicle", "delete vehicle, remove car"),
        ]

        for name, desc, triggers in snippets:
            code = f'''"""
@snippet: {name}
@mcp: car_log_core
@description: {desc}
@triggers: {triggers}
"""
async def run(): pass
'''
            (snippet_dir / f"{name}.py").write_text(code)

        self.library.scan()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_exact_name_match(self):
        """Match by exact snippet name."""
        results = self.library.match("list_vehicles")
        assert len(results) > 0
        assert results[0].snippet.name == "list_vehicles"
        assert results[0].match_type == "exact"
        assert results[0].score == 1.0

    def test_trigger_match(self):
        """Match by trigger keyword."""
        results = self.library.match("show cars")
        assert len(results) > 0
        assert results[0].snippet.name == "list_vehicles"
        assert results[0].match_type == "trigger"

    def test_description_match(self):
        """Match by description words."""
        results = self.library.match("vehicles")
        assert len(results) > 0
        # Should find multiple vehicle-related snippets
        names = [r.snippet.name for r in results]
        assert any("vehicle" in n for n in names)

    def test_fuzzy_match(self):
        """Fuzzy matching on partial input."""
        results = self.library.match("list vehs")
        # Should still find list_vehicles
        assert len(results) > 0

    def test_filter_by_mcp(self):
        """Filter matches by MCP server."""
        results = self.library.match("list", mcp="car_log_core")
        assert all(r.snippet.mcp == "car_log_core" for r in results)

        # Non-matching MCP returns empty
        results = self.library.match("list", mcp="geo_routing")
        assert len(results) == 0

    def test_top_k_limit(self):
        """Limit number of results."""
        results = self.library.match("vehicle", top_k=2)
        assert len(results) <= 2

    def test_no_match_low_score(self):
        """No results for unrelated query."""
        results = self.library.match("xyzzyx")
        # May return empty or very low score results
        if results:
            assert all(r.score < 0.5 for r in results)


class TestCodeLibraryStore:
    """Test snippet storage."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.library = CodeLibrary(self.temp_dir)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_store_new_snippet(self):
        """Store a new snippet."""
        code = '''async def run():
    return await car_log_core.list_vehicles({})
'''
        success, result = self.library.store(
            code=code,
            name="test_snippet",
            mcp="car_log_core",
            description="Test snippet",
            triggers=["test", "demo"]
        )

        assert success is True
        assert "test_snippet.py" in result

        # Verify it's in the index
        snippet = self.library.get_snippet("test_snippet")
        assert snippet is not None
        assert snippet.description == "Test snippet"

    def test_store_with_skill(self):
        """Store snippet with skill category."""
        code = "async def run(): pass"
        success, result = self.library.store(
            code=code,
            name="skilled_snippet",
            mcp="geo_routing",
            description="Test with skill",
            triggers=["test"],
            skill="geocoding"
        )

        assert success is True
        assert "geocoding" in result  # Skill should be in path

    def test_store_invalid_mcp(self):
        """Reject invalid MCP name."""
        success, msg = self.library.store(
            code="pass",
            name="invalid",
            mcp="invalid_mcp",
            description="Test",
            triggers=["test"]
        )

        assert success is False
        assert "Invalid MCP" in msg

    def test_store_invalid_name(self):
        """Reject invalid snippet name."""
        success, msg = self.library.store(
            code="pass",
            name="invalid-name",  # hyphen not allowed
            mcp="car_log_core",
            description="Test",
            triggers=["test"]
        )

        assert success is False
        assert "alphanumeric" in msg

    def test_store_no_overwrite(self):
        """Reject storing duplicate without overwrite."""
        code = "async def run(): pass"

        # First store
        self.library.store(
            code=code,
            name="duplicate",
            mcp="car_log_core",
            description="First",
            triggers=["test"]
        )

        # Second store (should fail)
        success, msg = self.library.store(
            code=code,
            name="duplicate",
            mcp="car_log_core",
            description="Second",
            triggers=["test"]
        )

        assert success is False
        assert "already exists" in msg

    def test_store_with_overwrite(self):
        """Allow overwriting existing snippet."""
        code = "async def run(): pass"

        # First store
        self.library.store(
            code=code,
            name="overwrite_me",
            mcp="car_log_core",
            description="First",
            triggers=["test"]
        )

        # Overwrite
        success, _ = self.library.store(
            code=code,
            name="overwrite_me",
            mcp="car_log_core",
            description="Updated",
            triggers=["test"],
            overwrite=True
        )

        assert success is True
        snippet = self.library.get_snippet("overwrite_me")
        assert snippet.description == "Updated"


class TestCodeLibraryList:
    """Test snippet listing."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.library = CodeLibrary(self.temp_dir)

        # Create test structure
        for mcp in ["car_log_core", "geo_routing"]:
            snippet_dir = Path(self.temp_dir) / mcp
            snippet_dir.mkdir(parents=True)

            code = f'''"""
@snippet: {mcp}_snippet
@mcp: {mcp}
@description: Test for {mcp}
@triggers: test
@skill: test_skill
"""
async def run(): pass
'''
            (snippet_dir / f"{mcp}_snippet.py").write_text(code)

        self.library.scan()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_list_all(self):
        """List all snippets."""
        snippets = self.library.list_snippets()
        assert len(snippets) == 2

    def test_list_by_mcp(self):
        """Filter by MCP server."""
        snippets = self.library.list_snippets(mcp="car_log_core")
        assert len(snippets) == 1
        assert snippets[0].mcp == "car_log_core"

    def test_list_by_skill(self):
        """Filter by skill."""
        snippets = self.library.list_snippets(skill="test_skill")
        assert len(snippets) == 2


class TestCodeLibraryDelete:
    """Test snippet deletion."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.library = CodeLibrary(self.temp_dir)

        # Create a snippet
        snippet_dir = Path(self.temp_dir) / "car_log_core"
        snippet_dir.mkdir(parents=True)

        code = '''"""
@snippet: to_delete
@mcp: car_log_core
@description: Will be deleted
@triggers: test
"""
async def run(): pass
'''
        (snippet_dir / "to_delete.py").write_text(code)
        self.library.scan()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_delete_existing(self):
        """Delete existing snippet."""
        assert self.library.get_snippet("to_delete") is not None

        result = self.library.delete("to_delete")
        assert result is True

        # Verify deleted
        assert self.library.get_snippet("to_delete") is None

    def test_delete_nonexistent(self):
        """Delete nonexistent returns False."""
        result = self.library.delete("nonexistent")
        assert result is False


class TestCodeLibraryFormat:
    """Test formatting for prompts."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.library = CodeLibrary(self.temp_dir)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_format_empty(self):
        """Format empty library."""
        output = self.library.format_for_prompt()
        assert "No code snippets" in output

    def test_format_with_snippets(self):
        """Format library with snippets."""
        # Add a snippet
        snippet_dir = Path(self.temp_dir) / "car_log_core"
        snippet_dir.mkdir(parents=True)

        code = '''"""
@snippet: test_format
@mcp: car_log_core
@description: Test formatting
@triggers: test, format
"""
async def run(): pass
'''
        (snippet_dir / "test_format.py").write_text(code)
        self.library.scan()

        output = self.library.format_for_prompt()
        assert "test_format" in output
        assert "car_log_core" in output
        assert "Test formatting" in output

    def test_get_index_summary(self):
        """Get index summary."""
        # Add snippets
        snippet_dir = Path(self.temp_dir) / "car_log_core"
        snippet_dir.mkdir(parents=True)

        code = '''"""
@snippet: summary_test
@mcp: car_log_core
@description: Summary test
@triggers: test
"""
async def run(): pass
'''
        (snippet_dir / "summary_test.py").write_text(code)
        self.library.scan()

        summary = self.library.get_index_summary()
        assert summary["total_snippets"] == 1
        assert "car_log_core" in summary["by_mcp"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
