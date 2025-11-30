"""
Dashboard View - Stats cards overview.

Shows summary statistics: vehicle count, checkpoint count, trip count,
total distance, and fuel efficiency.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import gradio as gr


@dataclass
class DashboardStats:
    """Dashboard statistics data."""
    vehicle_count: int = 0
    checkpoint_count: int = 0
    trip_count: int = 0
    total_distance_km: float = 0
    avg_efficiency: float = 0  # L/100km
    business_trip_pct: float = 0
    last_checkpoint_date: str = ""


class DashboardView:
    """
    Dashboard stats overview component.

    Displays summary cards with key metrics.
    """

    def __init__(self, adapters: Dict[str, Any]):
        """
        Initialize DashboardView.

        Args:
            adapters: Dictionary of MCP adapters (needs "car-log-core")
        """
        self.car_log_core = adapters.get("car-log-core")

    async def fetch_stats(self, vehicle_id: Optional[str] = None) -> DashboardStats:
        """
        Fetch dashboard statistics.

        Args:
            vehicle_id: Filter by vehicle (optional)

        Returns:
            DashboardStats with all metrics
        """
        stats = DashboardStats()

        if not self.car_log_core:
            return stats

        try:
            # Fetch vehicles
            vehicles_result = await self.car_log_core.call_tool("list_vehicles", {})
            if vehicles_result.success:
                vehicles = vehicles_result.data.get("vehicles", [])
                stats.vehicle_count = len(vehicles)

            # Fetch checkpoints
            cp_params = {"limit": 1000}
            if vehicle_id:
                cp_params["vehicle_id"] = vehicle_id
            cp_result = await self.car_log_core.call_tool("list_checkpoints", cp_params)
            if cp_result.success:
                checkpoints = cp_result.data.get("checkpoints", [])
                stats.checkpoint_count = len(checkpoints)
                # Get last checkpoint date
                if checkpoints:
                    dates = [cp.get("datetime", "") for cp in checkpoints if cp.get("datetime")]
                    if dates:
                        stats.last_checkpoint_date = max(dates)[:10]

            # Fetch trips
            trip_params = {"limit": 1000}
            if vehicle_id:
                trip_params["vehicle_id"] = vehicle_id
            trips_result = await self.car_log_core.call_tool("list_trips", trip_params)
            if trips_result.success:
                trips = trips_result.data.get("trips", [])
                stats.trip_count = len(trips)

                # Calculate totals
                total_km = 0
                efficiencies = []
                business_count = 0

                for trip in trips:
                    distance = trip.get("distance_km", 0)
                    if isinstance(distance, (int, float)):
                        total_km += distance

                    eff = trip.get("fuel_efficiency_l_per_100km")
                    if isinstance(eff, (int, float)) and eff > 0:
                        efficiencies.append(eff)

                    if trip.get("purpose") == "Business":
                        business_count += 1

                stats.total_distance_km = total_km
                if efficiencies:
                    stats.avg_efficiency = sum(efficiencies) / len(efficiencies)
                if stats.trip_count > 0:
                    stats.business_trip_pct = (business_count / stats.trip_count) * 100

        except Exception as e:
            print(f"Error fetching dashboard stats: {e}")

        return stats

    def create_component(self) -> tuple:
        """
        Create Gradio components for dashboard view.

        Returns:
            Tuple of (container, stat_components)
        """
        with gr.Column(visible=False) as container:
            gr.Markdown("## Dashboard")
            gr.Markdown("Overview of your vehicle mileage tracking.")

            # Stats cards row 1
            with gr.Row():
                with gr.Column(scale=1):
                    vehicles_card = gr.Markdown(
                        self._stat_card("Vehicles", "0", "Registered"),
                        elem_classes=["stat-card"],
                    )
                with gr.Column(scale=1):
                    checkpoints_card = gr.Markdown(
                        self._stat_card("Checkpoints", "0", "Recorded"),
                        elem_classes=["stat-card"],
                    )
                with gr.Column(scale=1):
                    trips_card = gr.Markdown(
                        self._stat_card("Trips", "0", "Logged"),
                        elem_classes=["stat-card"],
                    )

            # Stats cards row 2
            with gr.Row():
                with gr.Column(scale=1):
                    distance_card = gr.Markdown(
                        self._stat_card("Total Distance", "0 km", "All time"),
                        elem_classes=["stat-card"],
                    )
                with gr.Column(scale=1):
                    efficiency_card = gr.Markdown(
                        self._stat_card("Avg Efficiency", "- L/100km", "Fuel usage"),
                        elem_classes=["stat-card"],
                    )
                with gr.Column(scale=1):
                    business_card = gr.Markdown(
                        self._stat_card("Business Trips", "0%", "Of total"),
                        elem_classes=["stat-card"],
                    )

            # Last activity
            with gr.Row():
                last_activity = gr.Markdown("**Last Checkpoint:** None recorded")
                refresh_btn = gr.Button("Refresh Dashboard", size="sm")

            # Quick actions hint
            gr.Markdown("""
---
**Quick Actions:**
- Use chat to add a checkpoint
- Navigate to Checkpoints or Trips for detailed views
- Generate reports for tax compliance
            """)

        stat_components = (
            vehicles_card, checkpoints_card, trips_card,
            distance_card, efficiency_card, business_card,
            last_activity, refresh_btn
        )
        return container, stat_components

    def _stat_card(self, title: str, value: str, subtitle: str) -> str:
        """Generate markdown for a stat card."""
        return f"""
### {title}
# {value}
*{subtitle}*
"""


async def refresh_dashboard(
    view: DashboardView,
    vehicle_id: Optional[str],
) -> tuple:
    """
    Refresh dashboard stats.

    Args:
        view: DashboardView instance
        vehicle_id: Selected vehicle ID

    Returns:
        Tuple of stat card markdown updates
    """
    stats = await view.fetch_stats(vehicle_id)

    # Format values
    distance_str = f"{stats.total_distance_km:,.0f} km"
    efficiency_str = f"{stats.avg_efficiency:.1f} L/100km" if stats.avg_efficiency > 0 else "- L/100km"
    business_str = f"{stats.business_trip_pct:.0f}%"
    last_cp = f"**Last Checkpoint:** {stats.last_checkpoint_date}" if stats.last_checkpoint_date else "**Last Checkpoint:** None recorded"

    return (
        view._stat_card("Vehicles", str(stats.vehicle_count), "Registered"),
        view._stat_card("Checkpoints", str(stats.checkpoint_count), "Recorded"),
        view._stat_card("Trips", str(stats.trip_count), "Logged"),
        view._stat_card("Total Distance", distance_str, "All time"),
        view._stat_card("Avg Efficiency", efficiency_str, "Fuel usage"),
        view._stat_card("Business Trips", business_str, "Of total"),
        last_cp,
    )
