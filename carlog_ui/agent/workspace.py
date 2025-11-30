"""
Workspace Manager for Car Log Agent

Manages the workspace directory for:
- Saving intermediate results between code executions
- Persisting state across sessions (via Docker volume)
- Storing user-specific data and preferences
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class WorkspaceSession:
    """Metadata for a workspace session."""
    session_id: str
    created_at: str
    last_accessed: str
    vehicle_id: Optional[str] = None
    user_id: Optional[str] = None
    files_count: int = 0


class WorkspaceManager:
    """
    Manages workspace for agent state persistence.

    The workspace is mounted as a Docker volume, enabling:
    - State persistence across container restarts
    - File sharing between code executions
    - Session continuity for multi-step workflows
    """

    def __init__(self, workspace_path: str = "/app/workspace"):
        """
        Initialize workspace manager.

        Args:
            workspace_path: Root path for workspace directory
        """
        self.workspace_path = Path(workspace_path)
        self._ensure_workspace_exists()

        # Session tracking
        self.current_session: Optional[WorkspaceSession] = None

    def _ensure_workspace_exists(self):
        """Ensure workspace directory structure exists."""
        # Create main directories
        (self.workspace_path / "sessions").mkdir(parents=True, exist_ok=True)
        (self.workspace_path / "cache").mkdir(parents=True, exist_ok=True)
        (self.workspace_path / "exports").mkdir(parents=True, exist_ok=True)
        (self.workspace_path / "temp").mkdir(parents=True, exist_ok=True)

    def start_session(
        self,
        session_id: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> WorkspaceSession:
        """
        Start or resume a workspace session.

        Args:
            session_id: Optional session ID to resume
            vehicle_id: Current vehicle context
            user_id: User identifier

        Returns:
            WorkspaceSession metadata
        """
        now = datetime.now().isoformat()

        if session_id:
            # Try to resume existing session
            session_path = self.workspace_path / "sessions" / session_id
            if session_path.exists():
                metadata_file = session_path / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.current_session = WorkspaceSession(**data)
                        self.current_session.last_accessed = now
                        self._save_session_metadata()
                        return self.current_session

        # Create new session
        session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        session_path = self.workspace_path / "sessions" / session_id
        session_path.mkdir(parents=True, exist_ok=True)

        self.current_session = WorkspaceSession(
            session_id=session_id,
            created_at=now,
            last_accessed=now,
            vehicle_id=vehicle_id,
            user_id=user_id,
            files_count=0,
        )

        self._save_session_metadata()
        return self.current_session

    def _save_session_metadata(self):
        """Save current session metadata."""
        if not self.current_session:
            return

        session_path = self.workspace_path / "sessions" / self.current_session.session_id
        metadata_file = session_path / "metadata.json"

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(asdict(self.current_session), f, indent=2)

    def get_session_path(self) -> Path:
        """Get path for current session."""
        if not self.current_session:
            self.start_session()
        return self.workspace_path / "sessions" / self.current_session.session_id

    def save_file(
        self,
        filename: str,
        data: Any,
        as_json: bool = True,
    ) -> str:
        """
        Save data to workspace file.

        Args:
            filename: Name of file to save
            data: Data to save (will be JSON-serialized if as_json=True)
            as_json: Whether to serialize as JSON

        Returns:
            Full path to saved file
        """
        session_path = self.get_session_path()
        filepath = session_path / filename

        if as_json:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(str(data))

        # Update file count
        if self.current_session:
            self.current_session.files_count = len(list(session_path.glob("*")))
            self._save_session_metadata()

        return str(filepath)

    def load_file(self, filename: str, as_json: bool = True) -> Any:
        """
        Load data from workspace file.

        Args:
            filename: Name of file to load
            as_json: Whether to parse as JSON

        Returns:
            File contents (parsed if as_json=True)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        session_path = self.get_session_path()
        filepath = session_path / filename

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filename}")

        with open(filepath, "r", encoding="utf-8") as f:
            if as_json:
                return json.load(f)
            return f.read()

    def list_files(self) -> List[Dict[str, Any]]:
        """
        List all files in current session.

        Returns:
            List of file info dictionaries
        """
        session_path = self.get_session_path()
        files = []

        for filepath in session_path.glob("*"):
            if filepath.is_file() and filepath.name != "metadata.json":
                stat = filepath.stat()
                files.append({
                    "name": filepath.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })

        return files

    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from workspace.

        Args:
            filename: Name of file to delete

        Returns:
            True if deleted, False if not found
        """
        session_path = self.get_session_path()
        filepath = session_path / filename

        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def clear_session(self):
        """Clear all files in current session."""
        session_path = self.get_session_path()

        for filepath in session_path.glob("*"):
            if filepath.is_file() and filepath.name != "metadata.json":
                filepath.unlink()

        if self.current_session:
            self.current_session.files_count = 0
            self._save_session_metadata()

    def save_to_cache(self, key: str, data: Any, ttl_hours: int = 24) -> str:
        """
        Save data to cache with TTL.

        Args:
            key: Cache key
            data: Data to cache
            ttl_hours: Time to live in hours

        Returns:
            Cache file path
        """
        cache_path = self.workspace_path / "cache"
        cache_file = cache_path / f"{key}.json"

        cache_entry = {
            "data": data,
            "expires_at": (datetime.now() + timedelta(hours=ttl_hours)).isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_entry, f, indent=2, ensure_ascii=False, default=str)

        return str(cache_file)

    def load_from_cache(self, key: str) -> Optional[Any]:
        """
        Load data from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found/expired
        """
        cache_path = self.workspace_path / "cache"
        cache_file = cache_path / f"{key}.json"

        if not cache_file.exists():
            return None

        with open(cache_file, "r", encoding="utf-8") as f:
            cache_entry = json.load(f)

        expires_at = datetime.fromisoformat(cache_entry["expires_at"])
        if datetime.now() > expires_at:
            cache_file.unlink()  # Delete expired cache
            return None

        return cache_entry["data"]

    def cleanup_expired_cache(self):
        """Remove all expired cache entries."""
        cache_path = self.workspace_path / "cache"

        for cache_file in cache_path.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_entry = json.load(f)

                expires_at = datetime.fromisoformat(cache_entry["expires_at"])
                if datetime.now() > expires_at:
                    cache_file.unlink()
            except (json.JSONDecodeError, KeyError):
                # Invalid cache file, delete it
                cache_file.unlink()

    def cleanup_old_sessions(self, days: int = 7):
        """
        Remove sessions older than specified days.

        Args:
            days: Delete sessions older than this many days
        """
        sessions_path = self.workspace_path / "sessions"
        cutoff = datetime.now() - timedelta(days=days)

        for session_dir in sessions_path.iterdir():
            if not session_dir.is_dir():
                continue

            metadata_file = session_dir / "metadata.json"
            should_delete = False

            if metadata_file.exists():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    last_accessed = datetime.fromisoformat(data["last_accessed"])
                    if last_accessed < cutoff:
                        should_delete = True
                except (json.JSONDecodeError, KeyError):
                    should_delete = True
            else:
                # No metadata, check directory mtime
                if datetime.fromtimestamp(session_dir.stat().st_mtime) < cutoff:
                    should_delete = True

            if should_delete:
                shutil.rmtree(session_dir)

    def export_session(self, output_path: str) -> str:
        """
        Export current session to a zip file.

        Args:
            output_path: Where to save the export

        Returns:
            Path to exported file
        """
        session_path = self.get_session_path()
        export_name = f"session_{self.current_session.session_id}"

        # Create zip archive
        shutil.make_archive(
            os.path.join(output_path, export_name),
            "zip",
            session_path,
        )

        return os.path.join(output_path, f"{export_name}.zip")

    def get_workspace_stats(self) -> Dict[str, Any]:
        """
        Get workspace statistics.

        Returns:
            Dictionary with workspace stats
        """
        sessions_count = len(list((self.workspace_path / "sessions").glob("*")))
        cache_count = len(list((self.workspace_path / "cache").glob("*.json")))

        # Calculate total size
        total_size = 0
        for root, dirs, files in os.walk(self.workspace_path):
            for f in files:
                total_size += os.path.getsize(os.path.join(root, f))

        return {
            "workspace_path": str(self.workspace_path),
            "sessions_count": sessions_count,
            "cache_entries": cache_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "current_session": self.current_session.session_id if self.current_session else None,
        }
