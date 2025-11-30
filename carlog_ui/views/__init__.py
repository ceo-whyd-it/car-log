"""
Canvas views for data display in Gradio UI.

Provides hybrid navigation views:
- Dashboard: Stats overview
- Checkpoints: Data grid with filters
- Trips: Data grid with filters
- Reports: Report generation and download
"""

from .state import ViewState, get_visibility_updates
from .dashboard import DashboardView, refresh_dashboard
from .checkpoints import CheckpointsView, refresh_checkpoints
from .trips import TripsView, refresh_trips
from .reports import ReportsView, refresh_reports_list, get_report_file

__all__ = [
    # State management
    "ViewState",
    "get_visibility_updates",
    # Dashboard
    "DashboardView",
    "refresh_dashboard",
    # Checkpoints
    "CheckpointsView",
    "refresh_checkpoints",
    # Trips
    "TripsView",
    "refresh_trips",
    # Reports
    "ReportsView",
    "refresh_reports_list",
    "get_report_file",
]
