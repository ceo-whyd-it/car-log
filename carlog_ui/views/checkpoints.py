"""
Checkpoints View - Data grid for checkpoint list with filters.

Shows checkpoints in a gr.Dataframe with date, odometer, type, fuel, location columns.
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import gradio as gr


class CheckpointsView:
    """
    Checkpoints data grid view component.

    Displays checkpoint list with filtering by vehicle, date range, and type.
    """

    def __init__(self, adapters: Dict[str, Any]):
        """
        Initialize CheckpointsView.

        Args:
            adapters: Dictionary of MCP adapters (needs "car-log-core")
        """
        self.car_log_core = adapters.get("car-log-core")

    async def fetch_data(
        self,
        vehicle_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        checkpoint_type: Optional[str] = None,
        limit: int = 50,
    ) -> pd.DataFrame:
        """
        Fetch checkpoints and convert to DataFrame.

        Args:
            vehicle_id: Filter by vehicle (optional)
            date_from: Start date filter ISO format (optional)
            date_to: End date filter ISO format (optional)
            checkpoint_type: "refuel" or "manual" (optional)
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
        if checkpoint_type:
            params["checkpoint_type"] = checkpoint_type

        try:
            result = await self.car_log_core.call_tool("list_checkpoints", params)

            if not result.success:
                return self._empty_dataframe()

            checkpoints = result.data.get("checkpoints", [])
            return self._to_dataframe(checkpoints)

        except Exception as e:
            print(f"Error fetching checkpoints: {e}")
            return self._empty_dataframe()

    def _to_dataframe(self, checkpoints: List[Dict]) -> pd.DataFrame:
        """Convert checkpoint list to pandas DataFrame."""
        if not checkpoints:
            return self._empty_dataframe()

        rows = []
        for cp in checkpoints:
            datetime_str = cp.get("datetime", "")
            date_part = datetime_str[:10] if len(datetime_str) >= 10 else ""
            time_part = datetime_str[11:16] if len(datetime_str) >= 16 else ""

            # Get fuel info if refuel checkpoint
            receipt = cp.get("receipt", {})
            fuel_liters = receipt.get("fuel_liters", "")
            fuel_type = receipt.get("fuel_type", "")

            # Get location
            location = cp.get("location", {})
            address = location.get("address", "")

            rows.append({
                "ID": cp.get("checkpoint_id", "")[:8] + "...",  # Truncate UUID
                "Date": date_part,
                "Time": time_part,
                "Odometer (km)": cp.get("odometer_km", 0),
                "Type": cp.get("checkpoint_type", ""),
                "Fuel (L)": fuel_liters,
                "Fuel Type": fuel_type,
                "Location": address[:40] + "..." if len(address) > 40 else address,
            })

        return pd.DataFrame(rows)

    def _empty_dataframe(self) -> pd.DataFrame:
        """Return empty DataFrame with correct columns."""
        return pd.DataFrame(columns=[
            "ID", "Date", "Time", "Odometer (km)", "Type",
            "Fuel (L)", "Fuel Type", "Location"
        ])

    def create_component(self) -> tuple:
        """
        Create Gradio components for checkpoints view.

        Returns:
            Tuple of (container, dataframe, filter_components)
        """
        with gr.Column(visible=False) as container:
            gr.Markdown("## Checkpoints")
            gr.Markdown("View and filter your vehicle checkpoints (refuels and manual entries).")

            # Filters row
            with gr.Row():
                type_filter = gr.Dropdown(
                    label="Type",
                    choices=["All", "refuel", "manual"],
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
                label="Checkpoints",
                interactive=False,
                wrap=True,
            )

            # Action hint
            gr.Markdown(
                "*Use chat to add new checkpoints: type 'Add checkpoint' or scan a receipt.*",
                elem_classes=["hint-text"],
            )

        return container, dataframe, (type_filter, date_from, date_to, refresh_btn)


async def refresh_checkpoints(
    view: CheckpointsView,
    vehicle_id: Optional[str],
    type_filter: str,
    date_from: str,
    date_to: str,
) -> pd.DataFrame:
    """
    Refresh checkpoint data with current filters.

    Args:
        view: CheckpointsView instance
        vehicle_id: Selected vehicle ID
        type_filter: "All", "refuel", or "manual"
        date_from: Start date or empty string
        date_to: End date or empty string

    Returns:
        Updated DataFrame
    """
    cp_type = None if type_filter == "All" else type_filter
    df_from = date_from if date_from else None
    df_to = date_to if date_to else None

    return await view.fetch_data(
        vehicle_id=vehicle_id,
        date_from=df_from,
        date_to=df_to,
        checkpoint_type=cp_type,
    )
