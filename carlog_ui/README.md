# Car Log Gradio UI

Hybrid web interface for Slovak tax-compliant vehicle mileage logging.

## Architecture

The UI uses a **hybrid navigation** pattern:
- **Navigation views** for data display (tables, stats, grids)
- **Chat interface** for actions (add checkpoint, generate report, reconstruct trips)

```
+------------------------------------------------------------------+
|  HEADER: Car Log - Slovak Mileage Tracker    [Vehicle Dropdown]   |
+------------------------------------------------------------------+
|  SIDEBAR   |   MAIN CONTENT AREA                                  |
|            |                                                      |
| [Dashboard]|   VIEW CONTENT (visibility toggled)                  |
| [Checkpoints]  - Dashboard: stats cards                           |
| [Trips]    |   - Checkpoints: data grid + filters                 |
| [Reports]  |   - Trips: data grid + date range                    |
| [Chat]     |   - Reports: file list + download                    |
|            |   - Chat: chatbot interface (default)                |
|            |                                                      |
|            |   [CHAT INPUT - always visible at bottom]            |
+------------------------------------------------------------------+
```

## Directory Structure

```
carlog_ui/
├── app.py                 # Main Gradio application
├── config.py              # Configuration management
├── adapters/              # MCP server adapters
│   ├── base.py            # Base adapter classes
│   ├── car_log_core.py    # CRUD operations adapter
│   └── ...                # Other server adapters
├── views/                 # Navigation views
│   ├── __init__.py        # View exports
│   ├── state.py           # ViewState dataclass
│   ├── dashboard.py       # Stats overview
│   ├── checkpoints.py     # Checkpoint data grid
│   ├── trips.py           # Trip data grid
│   └── reports.py         # Reports list
├── chat/                  # Chat components
│   └── handler.py         # ChatHandler for message processing
├── components/            # Reusable UI components
│   └── quick_actions.py   # Quick action buttons
└── agent/                 # LLM agent (optional)
```

## View Pattern

Each view in `views/` follows this pattern:

```python
class CheckpointsView:
    def __init__(self, adapters: Dict[str, Any]):
        self.car_log_core = adapters.get("car-log-core")

    async def fetch_data(self, vehicle_id=None, ...) -> pd.DataFrame:
        result = await self.car_log_core.call_tool("list_checkpoints", params)
        return self._to_dataframe(result.data.get("checkpoints", []))

    def create_component(self) -> tuple:
        # Returns (container, dataframe, filter_components)
        with gr.Column(visible=False) as container:
            ...
        return container, dataframe, filters
```

## Navigation Wiring

Navigation buttons toggle view visibility and fetch data:

```python
async def nav_to_checkpoints(state_dict):
    state = ViewState.from_dict(state_dict)
    state.active_section = "checkpoints"

    df = await checkpoints_view.fetch_data(vehicle_id=state.selected_vehicle_id)
    vis = get_visibility_updates("checkpoints")  # (False, True, False, False, False)

    return state.to_dict(), *[gr.update(visible=v) for v in vis], df

btn_checkpoints.click(nav_to_checkpoints, inputs=[view_state], outputs=[...])
```

## State Management

`ViewState` in `views/state.py` tracks:
- `active_section`: Current view (dashboard, checkpoints, trips, reports, chat)
- `selected_vehicle_id`: Filter context for all views
- Filter values for each view (date ranges, type filters)

## Running the UI

```bash
# From project root
python -m carlog_ui.app

# Or with Docker
docker-compose up gradio
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Required for agent mode | - |
| `DATA_PATH` | Data storage directory | `~/Documents/MileageLog/data` |
| `GRADIO_SERVER_PORT` | Server port | `7860` |
