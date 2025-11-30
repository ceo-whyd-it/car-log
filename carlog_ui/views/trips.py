"""
Trips View - Data grid for trip list with filters.

Shows trips in a gr.Dataframe with date, from/to, distance, driver, purpose columns.
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import gradio as gr


class TripsView:
    """
    Trips data grid view component.

    Displays trip list with filtering by vehicle, date range, and purpose.
    """

    def __init__(self, adapters: Dict[str, Any]):
        """
        Initialize TripsView.

        Args:
            adapters: Dictionary of MCP adapters (needs "car-log-core")
        """
        self.car_log_core = adapters.get("car-log-core")

    async def fetch_data(
        self,
        vehicle_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        purpose: Optional[str] = None,
        limit: int = 50,
    ) -> pd.DataFrame:
        """
        Fetch trips and convert to DataFrame.

        Args:
            vehicle_id: Filter by vehicle (optional)
            date_from: Start date filter ISO format (optional)
            date_to: End date filter ISO format (optional)
            purpose: "Business" or "Personal" (optional)
            limit: Max rows to return

        Returns:
            pandas DataFrame for gr.Dataframe component
        """
        if not self.car_log_core:
            return self._empty_dataframe()

        # Build parameters
        params = {"limit": limit}
        if vehicle_id:
            params["vehicle_id"] = vehicle_id
        if date_from:
            params["start_date"] = date_from
        if date_to:
            params["end_date"] = date_to
        if purpose:
            params["purpose"] = purpose

        try:
            result = await self.car_log_core.call_tool("list_trips", params)

            if not result.success:
                return self._empty_dataframe()

            trips = result.data.get("trips", [])
            return self._to_dataframe(trips)

        except Exception as e:
            print(f"Error fetching trips: {e}")
            return self._empty_dataframe()

    def _to_dataframe(self, trips: List[Dict]) -> pd.DataFrame:
        """Convert trip list to pandas DataFrame."""
        if not trips:
            return self._empty_dataframe()

        rows = []
        for trip in trips:
            # Parse datetime
            start_datetime = trip.get("trip_start_datetime", "")
            date_part = start_datetime[:10] if len(start_datetime) >= 10 else ""

            # Get locations (truncate long addresses)
            start_loc = trip.get("trip_start_location", "")
            end_loc = trip.get("trip_end_location", "")
            start_short = start_loc[:25] + "..." if len(start_loc) > 25 else start_loc
            end_short = end_loc[:25] + "..." if len(end_loc) > 25 else end_loc

            # Fuel efficiency (L/100km format)
            efficiency = trip.get("fuel_efficiency_l_per_100km", "")
            efficiency_str = f"{efficiency:.1f}" if isinstance(efficiency, (int, float)) else ""

            rows.append({
                "ID": trip.get("trip_id", "")[:8] + "...",  # Truncate UUID
                "Date": date_part,
                "From": start_short,
                "To": end_short,
                "Distance (km)": trip.get("distance_km", 0),
                "Driver": trip.get("driver_name", ""),
                "Purpose": trip.get("purpose", ""),
                "L/100km": efficiency_str,
                "Method": trip.get("reconstruction_method", ""),
            })

        return pd.DataFrame(rows)

    def _empty_dataframe(self) -> pd.DataFrame:
        """Return empty DataFrame with correct columns."""
        return pd.DataFrame(columns=[
            "ID", "Date", "From", "To", "Distance (km)",
            "Driver", "Purpose", "L/100km", "Method"
        ])

    def create_component(self) -> tuple:
        """
        Create Gradio components for trips view.

        Returns:
            Tuple of (container, dataframe, filter_components)
        """
        with gr.Column(visible=False) as container:
            gr.Markdown("## Trips")
            gr.Markdown("View your logged trips with Slovak VAT compliance details.")

            # Filters row
            with gr.Row():
                purpose_filter = gr.Dropdown(
                    label="Purpose",
                    choices=["All", "Business", "Personal"],
                    value="All",
                    scale=1,
                )
                date_from = gr.Textbox(
                    label="From Date",
                    placeholder="YYYY-MM-DD",
                    scale=1,
                )
                date_to = gr.Textbox(
                    label="To Date",
                    placeholder="YYYY-MM-DD",
                    scale=1,
                )
                refresh_btn = gr.Button("Refresh", size="sm", scale=1)

            # Data grid
            dataframe = gr.Dataframe(
                value=self._empty_dataframe(),
                label="Trips",
                interactive=False,
                wrap=True,
            )

            # Summary row
            with gr.Row():
                total_distance = gr.Markdown("**Total Distance:** 0 km")
                avg_efficiency = gr.Markdown("**Avg Efficiency:** - L/100km")

            # Action hint
            gr.Markdown(
                "*Use chat to reconstruct trips: type 'Check for gaps' or 'Reconstruct trips'.*",
                elem_classes=["hint-text"],
            )

        return container, dataframe, (purpose_filter, date_from, date_to, refresh_btn, total_distance, avg_efficiency)


async def refresh_trips(
    view: TripsView,
    vehicle_id: Optional[str],
    purpose_filter: str,
    date_from: str,
    date_to: str,
) -> tuple:
    """
    Refresh trip data with current filters.

    Args:
        view: TripsView instance
        vehicle_id: Selected vehicle ID
        purpose_filter: "All", "Business", or "Personal"
        date_from: Start date or empty string
        date_to: End date or empty string

    Returns:
        Tuple of (DataFrame, total_distance_md, avg_efficiency_md)
    """
    purpose = None if purpose_filter == "All" else purpose_filter
    df_from = date_from if date_from else None
    df_to = date_to if date_to else None

    df = await view.fetch_data(
        vehicle_id=vehicle_id,
        date_from=df_from,
        date_to=df_to,
        purpose=purpose,
    )

    # Calculate summary stats
    total_km = 0
    efficiencies = []

    if not df.empty and "Distance (km)" in df.columns:
        total_km = df["Distance (km)"].sum()
        # Parse efficiency values
        for eff in df["L/100km"]:
            if eff and eff != "":
                try:
                    efficiencies.append(float(eff))
                except ValueError:
                    pass

    avg_eff = sum(efficiencies) / len(efficiencies) if efficiencies else 0
    avg_eff_str = f"{avg_eff:.1f}" if avg_eff > 0 else "-"

    return (
        df,
        f"**Total Distance:** {total_km:,.0f} km",
        f"**Avg Efficiency:** {avg_eff_str} L/100km",
    )
