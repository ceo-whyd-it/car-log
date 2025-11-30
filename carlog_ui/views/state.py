"""
ViewState - Centralized state management for hybrid Gradio UI.

Tracks active section, vehicle selection, and filter state for all views.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ViewState:
    """
    Centralized UI state for hybrid navigation views.

    Used with gr.State to persist state across Gradio callbacks.
    """

    # Navigation
    active_section: str = "chat"  # "dashboard", "checkpoints", "trips", "reports", "chat"

    # Vehicle context (shared across all views)
    selected_vehicle_id: Optional[str] = None
    vehicles_cache: List[Dict[str, Any]] = field(default_factory=list)

    # Checkpoint view filters
    cp_date_from: Optional[str] = None
    cp_date_to: Optional[str] = None
    cp_type_filter: Optional[str] = None  # "refuel", "manual", or None for all

    # Trip view filters
    trip_date_from: Optional[str] = None
    trip_date_to: Optional[str] = None
    trip_purpose_filter: Optional[str] = None  # "Business", "Personal", or None

    # Reports state
    reports_list: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dict for gr.State (Gradio requires JSON-serializable)."""
        return {
            "active_section": self.active_section,
            "selected_vehicle_id": self.selected_vehicle_id,
            "vehicles_cache": self.vehicles_cache,
            "cp_date_from": self.cp_date_from,
            "cp_date_to": self.cp_date_to,
            "cp_type_filter": self.cp_type_filter,
            "trip_date_from": self.trip_date_from,
            "trip_date_to": self.trip_date_to,
            "trip_purpose_filter": self.trip_purpose_filter,
            "reports_list": self.reports_list,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ViewState":
        """Create ViewState from dict."""
        if d is None:
            return cls()
        return cls(
            active_section=d.get("active_section", "chat"),
            selected_vehicle_id=d.get("selected_vehicle_id"),
            vehicles_cache=d.get("vehicles_cache", []),
            cp_date_from=d.get("cp_date_from"),
            cp_date_to=d.get("cp_date_to"),
            cp_type_filter=d.get("cp_type_filter"),
            trip_date_from=d.get("trip_date_from"),
            trip_date_to=d.get("trip_date_to"),
            trip_purpose_filter=d.get("trip_purpose_filter"),
            reports_list=d.get("reports_list", []),
        )


def get_visibility_updates(section: str) -> tuple:
    """
    Get visibility update tuples for section switching.

    Args:
        section: The section to show ("dashboard", "checkpoints", "trips", "reports", "chat")

    Returns:
        Tuple of (dashboard_visible, checkpoints_visible, trips_visible, reports_visible, chat_visible)
    """
    visibility_map = {
        "dashboard": (True, False, False, False, False),
        "checkpoints": (False, True, False, False, False),
        "trips": (False, False, True, False, False),
        "reports": (False, False, False, True, False),
        "chat": (False, False, False, False, True),
    }
    return visibility_map.get(section, (False, False, False, False, True))
