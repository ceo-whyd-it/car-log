"""
Snippet Manager for parsing and validating code snippet headers.

Handles the standardized header format used in code snippets:
- @snippet: Unique name for the snippet
- @mcp: MCP server name (car_log_core, geo_routing, etc.)
- @skill: Optional skill category
- @description: What the snippet does
- @triggers: Comma-separated keywords for matching
- @params: Optional parameter description
- @returns: Optional return value description
- @version: Version number (default 1.0)
"""

import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class SnippetHeader:
    """Parsed header from code snippet."""
    snippet: str
    mcp: str
    description: str
    triggers: List[str]
    skill: Optional[str] = None
    params: Optional[str] = None
    returns: Optional[str] = None
    version: str = "1.0"

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "snippet": self.snippet,
            "mcp": self.mcp,
            "description": self.description,
            "triggers": self.triggers,
            "skill": self.skill,
            "params": self.params,
            "returns": self.returns,
            "version": self.version
        }


class SnippetManager:
    """Parse, validate, and generate code snippet headers."""

    # Pattern to match @field: value in docstrings
    HEADER_PATTERN = re.compile(r'@(\w+):\s*(.+)')

    # Required fields for a valid header
    REQUIRED_FIELDS = {'snippet', 'mcp', 'description', 'triggers'}

    # Maximum header constraints
    MAX_HEADER_LINES = 10
    MAX_HEADER_CHARS = 700

    # Valid MCP server names
    VALID_MCPS = {
        'car_log_core',
        'geo_routing',
        'validation',
        'trip_reconstructor',
        'ekasa_api',
        'dashboard_ocr',
        'report_generator'
    }

    def parse_header(self, code: str) -> Optional[SnippetHeader]:
        """
        Extract header fields from first 10 lines of code.

        Args:
            code: Full code string with docstring header

        Returns:
            SnippetHeader if valid, None otherwise
        """
        lines = code.strip().split('\n')[:self.MAX_HEADER_LINES]
        header_text = '\n'.join(lines)

        # Check for docstring
        if not (header_text.startswith('"""') or header_text.startswith("'''")):
            return None

        # Extract fields
        fields: Dict[str, str] = {}
        for match in self.HEADER_PATTERN.finditer(header_text):
            field_name = match.group(1).lower()
            field_value = match.group(2).strip()
            fields[field_name] = field_value

        # Validate required fields
        if not self.REQUIRED_FIELDS.issubset(fields.keys()):
            return None

        # Parse triggers list (comma-separated)
        triggers = [t.strip() for t in fields['triggers'].split(',')]

        return SnippetHeader(
            snippet=fields['snippet'],
            mcp=fields['mcp'],
            description=fields['description'],
            triggers=triggers,
            skill=fields.get('skill'),
            params=fields.get('params'),
            returns=fields.get('returns'),
            version=fields.get('version', '1.0')
        )

    def generate_header(
        self,
        snippet: str,
        mcp: str,
        description: str,
        triggers: List[str],
        skill: Optional[str] = None,
        params: Optional[str] = None,
        returns: Optional[str] = None,
        version: str = "1.0"
    ) -> str:
        """
        Generate standardized header docstring.

        Args:
            snippet: Unique snippet name
            mcp: MCP server name
            description: What the snippet does
            triggers: Keywords for matching
            skill: Optional skill category
            params: Optional parameter description
            returns: Optional return description
            version: Version string

        Returns:
            Formatted docstring header

        Raises:
            ValueError: If header exceeds size limit
        """
        lines = ['"""']
        lines.append(f'@snippet: {snippet}')
        lines.append(f'@mcp: {mcp}')
        if skill:
            lines.append(f'@skill: {skill}')
        lines.append(f'@description: {description}')
        lines.append(f'@triggers: {", ".join(triggers)}')
        if params:
            lines.append(f'@params: {params}')
        if returns:
            lines.append(f'@returns: {returns}')
        lines.append(f'@version: {version}')
        lines.append('"""')

        header = '\n'.join(lines)

        # Validate size
        if len(header) > self.MAX_HEADER_CHARS:
            raise ValueError(f"Header exceeds {self.MAX_HEADER_CHARS} chars (got {len(header)})")

        return header

    def validate_header(self, header: SnippetHeader) -> Tuple[bool, List[str]]:
        """
        Validate header has all required fields and valid values.

        Args:
            header: Parsed SnippetHeader

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if not header.snippet:
            errors.append("Missing @snippet field")
        elif not header.snippet.replace('_', '').isalnum():
            errors.append("@snippet must be alphanumeric with underscores only")

        if not header.mcp:
            errors.append("Missing @mcp field")
        elif header.mcp not in self.VALID_MCPS:
            errors.append(f"Invalid MCP: {header.mcp}. Valid: {', '.join(sorted(self.VALID_MCPS))}")

        if not header.description:
            errors.append("Missing @description field")

        if not header.triggers:
            errors.append("Missing @triggers field")
        elif len(header.triggers) == 0:
            errors.append("@triggers must have at least one keyword")

        return len(errors) == 0, errors

    def should_store(self, code: str, success: bool, stdout: str) -> bool:
        """
        Decide if code should be stored in library.

        Criteria:
        - Must have executed successfully
        - Must be >= 5 lines (not trivial)
        - Must contain MCP adapter calls
        - Should be reusable (multi-step workflows are more valuable)

        Args:
            code: The executed code
            success: Whether execution was successful
            stdout: Output from execution

        Returns:
            True if code should be stored
        """
        if not success:
            return False

        # Count non-empty lines
        lines = [line for line in code.strip().split('\n') if line.strip()]
        if len(lines) < 5:
            return False

        # Must have MCP adapter call
        mcp_patterns = [
            'await car_log_core.',
            'await geo_routing.',
            'await validation.',
            'await trip_reconstructor.',
            'await ekasa_api.',
            'await dashboard_ocr.',
            'await report_generator.',
        ]
        has_mcp = any(pattern in code for pattern in mcp_patterns)

        if not has_mcp:
            return False

        # Multi-step workflows are more valuable
        await_count = code.count('await ')
        is_complex = await_count >= 2

        # Check if it produced useful output
        has_output = bool(stdout.strip()) and 'error' not in stdout.lower()

        return is_complex or has_output

    def extract_code_body(self, code: str) -> str:
        """
        Extract code body without the header docstring.

        Args:
            code: Full code with header

        Returns:
            Code body only
        """
        lines = code.strip().split('\n')

        # Find end of docstring
        in_docstring = False
        docstring_end = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_docstring:
                    docstring_end = i + 1
                    break
                else:
                    in_docstring = True
                    # Check if single-line docstring
                    if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                        docstring_end = i + 1
                        break

        return '\n'.join(lines[docstring_end:])
