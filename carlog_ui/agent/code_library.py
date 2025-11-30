"""
Code Library for storing and retrieving reusable code snippets.

The library organizes snippets by MCP server and provides:
- Scanning directories for snippets with valid headers
- Indexing snippets by name, triggers, and description
- Fuzzy matching user intents to existing snippets
- Storing new snippets after successful execution
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .snippet_manager import SnippetManager, SnippetHeader


@dataclass
class SnippetEntry:
    """A snippet in the library."""
    name: str
    mcp: str
    description: str
    triggers: List[str]
    file_path: str
    code: str
    header: SnippetHeader
    skill: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "mcp": self.mcp,
            "description": self.description,
            "triggers": self.triggers,
            "file_path": self.file_path,
            "skill": self.skill
        }


@dataclass
class MatchResult:
    """Result of matching user intent to snippets."""
    snippet: SnippetEntry
    score: float
    match_type: str  # "exact", "trigger", "description", "fuzzy"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.snippet.name,
            "mcp": self.snippet.mcp,
            "description": self.snippet.description,
            "score": self.score,
            "match_type": self.match_type,
            "file_path": self.snippet.file_path
        }


class CodeLibrary:
    """Manages the code snippet library."""

    # Minimum score for a match to be considered
    MIN_MATCH_SCORE = 0.3

    # Score weights
    EXACT_MATCH_SCORE = 1.0
    TRIGGER_MATCH_SCORE = 0.9
    DESCRIPTION_MATCH_SCORE = 0.7

    def __init__(self, library_path: str = "code_library"):
        """
        Initialize the code library.

        Args:
            library_path: Path to the code library directory
        """
        self.library_path = Path(library_path)
        self.snippet_manager = SnippetManager()
        self._index: Dict[str, SnippetEntry] = {}
        self._trigger_index: Dict[str, List[str]] = {}  # trigger -> [snippet_names]

    def scan(self) -> int:
        """
        Scan the library directory and index all valid snippets.

        Returns:
            Number of snippets indexed
        """
        self._index.clear()
        self._trigger_index.clear()

        if not self.library_path.exists():
            return 0

        count = 0
        for py_file in self.library_path.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue  # Skip __init__.py and private files

            try:
                code = py_file.read_text(encoding="utf-8")
                header = self.snippet_manager.parse_header(code)

                if header:
                    is_valid, errors = self.snippet_manager.validate_header(header)
                    if is_valid:
                        entry = SnippetEntry(
                            name=header.snippet,
                            mcp=header.mcp,
                            description=header.description,
                            triggers=header.triggers,
                            file_path=str(py_file),
                            code=code,
                            header=header,
                            skill=header.skill
                        )
                        self._index[header.snippet] = entry

                        # Index triggers
                        for trigger in header.triggers:
                            trigger_lower = trigger.lower().strip()
                            if trigger_lower not in self._trigger_index:
                                self._trigger_index[trigger_lower] = []
                            self._trigger_index[trigger_lower].append(header.snippet)

                        count += 1
            except Exception:
                continue  # Skip files that can't be read

        return count

    def get_snippet(self, name: str) -> Optional[SnippetEntry]:
        """
        Get a snippet by exact name.

        Args:
            name: Snippet name

        Returns:
            SnippetEntry if found, None otherwise
        """
        return self._index.get(name)

    def list_snippets(
        self,
        mcp: Optional[str] = None,
        skill: Optional[str] = None
    ) -> List[SnippetEntry]:
        """
        List snippets with optional filtering.

        Args:
            mcp: Filter by MCP server name
            skill: Filter by skill category

        Returns:
            List of matching snippets
        """
        results = list(self._index.values())

        if mcp:
            results = [s for s in results if s.mcp == mcp]

        if skill:
            results = [s for s in results if s.skill == skill]

        return results

    def match(
        self,
        user_intent: str,
        mcp: Optional[str] = None,
        top_k: int = 5
    ) -> List[MatchResult]:
        """
        Match user intent to snippets in the library.

        Uses multiple matching strategies:
        1. Exact name match
        2. Trigger keyword match
        3. Description similarity
        4. Fuzzy matching

        Args:
            user_intent: User's natural language intent
            mcp: Optional filter by MCP server
            top_k: Maximum number of results

        Returns:
            List of MatchResult sorted by score (descending)
        """
        results: List[MatchResult] = []
        intent_lower = user_intent.lower().strip()
        intent_words = set(intent_lower.split())

        # Get candidates (optionally filtered by MCP)
        candidates = self.list_snippets(mcp=mcp)

        for snippet in candidates:
            best_score = 0.0
            match_type = "fuzzy"

            # 1. Exact name match
            if intent_lower == snippet.name.lower():
                best_score = self.EXACT_MATCH_SCORE
                match_type = "exact"
            else:
                # 2. Trigger match
                for trigger in snippet.triggers:
                    trigger_lower = trigger.lower().strip()
                    if trigger_lower in intent_lower:
                        score = self.TRIGGER_MATCH_SCORE
                        if score > best_score:
                            best_score = score
                            match_type = "trigger"
                    elif intent_lower in trigger_lower:
                        score = self.TRIGGER_MATCH_SCORE * 0.9
                        if score > best_score:
                            best_score = score
                            match_type = "trigger"

                # 3. Description similarity
                if best_score < self.DESCRIPTION_MATCH_SCORE:
                    desc_lower = snippet.description.lower()
                    desc_words = set(desc_lower.split())
                    common_words = intent_words & desc_words
                    if common_words:
                        # Jaccard-like similarity
                        score = len(common_words) / len(intent_words | desc_words)
                        score *= self.DESCRIPTION_MATCH_SCORE
                        if score > best_score:
                            best_score = score
                            match_type = "description"

                # 4. Fuzzy matching on name and triggers
                if best_score < self.MIN_MATCH_SCORE:
                    # Check name similarity
                    name_ratio = SequenceMatcher(
                        None, intent_lower, snippet.name.lower()
                    ).ratio()
                    if name_ratio > best_score:
                        best_score = name_ratio
                        match_type = "fuzzy"

                    # Check trigger similarity
                    for trigger in snippet.triggers:
                        ratio = SequenceMatcher(
                            None, intent_lower, trigger.lower()
                        ).ratio()
                        if ratio > best_score:
                            best_score = ratio
                            match_type = "fuzzy"

            if best_score >= self.MIN_MATCH_SCORE:
                results.append(MatchResult(
                    snippet=snippet,
                    score=best_score,
                    match_type=match_type
                ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def store(
        self,
        code: str,
        name: str,
        mcp: str,
        description: str,
        triggers: List[str],
        skill: Optional[str] = None,
        overwrite: bool = False
    ) -> Tuple[bool, str]:
        """
        Store a new snippet in the library.

        Args:
            code: The code to store (without header)
            name: Unique snippet name
            mcp: MCP server name
            description: What the snippet does
            triggers: Keywords for matching
            skill: Optional skill category
            overwrite: Whether to overwrite existing snippet

        Returns:
            Tuple of (success, message_or_file_path)
        """
        # Validate name
        if not name.replace("_", "").isalnum():
            return False, "Name must be alphanumeric with underscores only"

        # Check if exists
        if name in self._index and not overwrite:
            return False, f"Snippet '{name}' already exists"

        # Validate MCP
        if mcp not in self.snippet_manager.VALID_MCPS:
            return False, f"Invalid MCP: {mcp}"

        # Generate header
        try:
            header_str = self.snippet_manager.generate_header(
                snippet=name,
                mcp=mcp,
                description=description,
                triggers=triggers,
                skill=skill
            )
        except ValueError as e:
            return False, str(e)

        # Combine header and code
        full_code = header_str + "\n" + code

        # Determine file path
        mcp_dir = self.library_path / mcp
        if skill:
            mcp_dir = mcp_dir / skill

        mcp_dir.mkdir(parents=True, exist_ok=True)
        file_path = mcp_dir / f"{name}.py"

        # Write file
        try:
            file_path.write_text(full_code, encoding="utf-8")
        except Exception as e:
            return False, f"Failed to write file: {e}"

        # Re-index to include new snippet
        self.scan()

        return True, str(file_path)

    def get_index_summary(self) -> Dict:
        """
        Get a summary of the library index for system prompts.

        Returns:
            Dictionary with index summary
        """
        summary = {
            "total_snippets": len(self._index),
            "by_mcp": {},
            "by_skill": {}
        }

        for snippet in self._index.values():
            # Count by MCP
            if snippet.mcp not in summary["by_mcp"]:
                summary["by_mcp"][snippet.mcp] = []
            summary["by_mcp"][snippet.mcp].append({
                "name": snippet.name,
                "description": snippet.description,
                "triggers": snippet.triggers
            })

            # Count by skill
            if snippet.skill:
                if snippet.skill not in summary["by_skill"]:
                    summary["by_skill"][snippet.skill] = []
                summary["by_skill"][snippet.skill].append(snippet.name)

        return summary

    def format_for_prompt(self, max_snippets: int = 20) -> str:
        """
        Format the library index for inclusion in system prompts.

        Args:
            max_snippets: Maximum number of snippets to include

        Returns:
            Formatted string for system prompt
        """
        if not self._index:
            return "No code snippets available in library."

        lines = ["## Available Code Snippets\n"]

        # Group by MCP
        by_mcp: Dict[str, List[SnippetEntry]] = {}
        for snippet in self._index.values():
            if snippet.mcp not in by_mcp:
                by_mcp[snippet.mcp] = []
            by_mcp[snippet.mcp].append(snippet)

        count = 0
        for mcp, snippets in sorted(by_mcp.items()):
            lines.append(f"\n### {mcp}\n")
            for snippet in snippets:
                if count >= max_snippets:
                    lines.append(f"\n... and {len(self._index) - count} more snippets")
                    return "\n".join(lines)

                triggers_str = ", ".join(snippet.triggers[:3])
                lines.append(f"- **{snippet.name}**: {snippet.description}")
                lines.append(f"  Triggers: {triggers_str}")
                count += 1

        return "\n".join(lines)

    def delete(self, name: str) -> bool:
        """
        Delete a snippet from the library.

        Args:
            name: Snippet name to delete

        Returns:
            True if deleted, False if not found
        """
        if name not in self._index:
            return False

        snippet = self._index[name]
        try:
            Path(snippet.file_path).unlink()
        except Exception:
            return False

        # Re-index
        self.scan()
        return True
