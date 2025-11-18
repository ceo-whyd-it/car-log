"""
Atomic file storage module for car-log-core.

CRITICAL: Always use atomic write pattern to prevent file corruption.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


def get_data_path() -> Path:
    """Get the base data path from environment or default."""
    data_path = os.getenv("DATA_PATH", "~/Documents/MileageLog/data")
    return Path(data_path).expanduser()


def atomic_write_json(file_path: Path, data: Dict[str, Any]) -> bool:
    """
    Write JSON file atomically (crash-safe).

    This pattern ensures that either the write succeeds completely
    or the original file remains intact. No partial/corrupted files.

    Args:
        file_path: Path to final file
        data: Data to write

    Returns:
        True if successful

    Raises:
        Exception: If write fails
    """
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory (ensures same filesystem for atomic rename)
    dir_path = file_path.parent
    fd, temp_path = tempfile.mkstemp(dir=dir_path, suffix='.tmp')

    try:
        # Write to temp file
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Atomic rename (POSIX guarantees atomicity)
        os.replace(temp_path, file_path)

        return True
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e


def read_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Read JSON file safely.

    Args:
        file_path: Path to file

    Returns:
        Parsed JSON data or None if file doesn't exist

    Raises:
        json.JSONDecodeError: If file is corrupted
    """
    if not file_path.exists():
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_json_files(directory: Path) -> list[Path]:
    """
    List all JSON files in directory (excluding temp files).

    Args:
        directory: Directory to search

    Returns:
        List of JSON file paths
    """
    if not directory.exists():
        return []

    return [f for f in directory.glob('*.json') if not f.name.endswith('.tmp')]


def get_month_folder(date: datetime) -> str:
    """
    Get month folder name from datetime.

    Args:
        date: Date object

    Returns:
        Folder name in YYYY-MM format
    """
    return date.strftime("%Y-%m")


def ensure_month_folder(base_path: Path, date: datetime) -> Path:
    """
    Ensure month folder exists.

    Args:
        base_path: Base path (e.g., data/checkpoints)
        date: Date for month folder

    Returns:
        Path to month folder
    """
    month_folder = get_month_folder(date)
    folder_path = base_path / month_folder
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path
