"""
Car Log - Gradio Web Application

Hybrid interface for Slovak tax-compliant vehicle mileage logging.
- Navigation views for data display (Dashboard, Checkpoints, Trips, Reports)
- Chat interface for actions (add checkpoint, generate report, reconstruct trips)
- LLM-powered agent using Code Execution with MCP pattern
"""

# Logging initialization - must be first
import os
from carlog_ui.logging_config import setup_logging, wait_for_mlflow

# Wait for MLflow before initializing logging
mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5050")
mlflow_ready = wait_for_mlflow(mlflow_uri, timeout=60)

# Initialize unified logging
logger = setup_logging(
    capture_stdout=True,
    mlflow_enabled=mlflow_ready,
)

logger.info("Car Log application starting...")

# Suppress Gradio 6.0 deprecation warnings (we're on 5.x, will fix when upgrading to 6.0)
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*Gradio 6.0.*")
warnings.filterwarnings("ignore", category=UserWarning, message=".*tuples.*deprecated.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*allow_tags.*")

import asyncio
from typing import List, Tuple, Optional, Dict, Any

import gradio as gr

from .config import get_config, AppConfig
from .chat.handler import ChatHandler
from .components.quick_actions import action_to_message
from .views import (
    ViewState,
    get_visibility_updates,
    DashboardView,
    CheckpointsView,
    TripsView,
    ReportsView,
    refresh_dashboard,
    refresh_checkpoints,
    refresh_trips,
    refresh_reports_list,
    get_report_file,
)

# Enable OpenTelemetry logging instrumentation
try:
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    LoggingInstrumentor().instrument(set_logging_format=True)
    logger.info("OpenTelemetry logging instrumentation enabled")
except Exception as e:
    logger.warning(f"OpenTelemetry logging instrumentation not available: {e}")


# Global state
config: Optional[AppConfig] = None
chat_handler: Optional[ChatHandler] = None
car_log_agent = None  # CarLogAgent instance
adapters: Dict[str, Any] = {}
use_agent_mode = True  # Toggle between agent (LLM) and legacy (regex) mode

# View instances (initialized after adapters)
dashboard_view: Optional[DashboardView] = None
checkpoints_view: Optional[CheckpointsView] = None
trips_view: Optional[TripsView] = None
reports_view: Optional[ReportsView] = None


async def initialize_app():
    """Initialize adapters and services."""
    global config, chat_handler, car_log_agent, adapters, use_agent_mode
    global dashboard_view, checkpoints_view, trips_view, reports_view

    config = get_config()
    # Agent mode is now fixed - uses in-process execution with real adapters

    # Initialize adapters (lazy import to handle missing dependencies)
    try:
        from .adapters import (
            CarLogCoreAdapter,
            TripReconstructorAdapter,
            ValidationAdapter,
            EkasaApiAdapter,
            DashboardOcrAdapter,
            ReportGeneratorAdapter,
            GeoRoutingAdapter,
        )

        # Initialize Python adapters
        adapters["car-log-core"] = CarLogCoreAdapter()
        await adapters["car-log-core"].initialize()

        adapters["trip-reconstructor"] = TripReconstructorAdapter()
        await adapters["trip-reconstructor"].initialize()

        adapters["validation"] = ValidationAdapter()
        await adapters["validation"].initialize()

        adapters["ekasa-api"] = EkasaApiAdapter()
        await adapters["ekasa-api"].initialize()

        adapters["dashboard-ocr"] = DashboardOcrAdapter()
        await adapters["dashboard-ocr"].initialize()

        adapters["report-generator"] = ReportGeneratorAdapter()
        await adapters["report-generator"].initialize()

        # Initialize HTTP adapter for geo-routing
        adapters["geo-routing"] = GeoRoutingAdapter(base_url=config.geo_routing_url)
        # Don't await initialize - it may fail if geo-routing not running

    except ImportError as e:
        print(f"Warning: Could not import adapters: {e}")

    # Initialize views
    dashboard_view = DashboardView(adapters)
    checkpoints_view = CheckpointsView(adapters)
    trips_view = TripsView(adapters)
    reports_view = ReportsView(adapters)

    # Initialize tracker (optional)
    tracker = None
    try:
        from .mlflow_tracking import ConversationTracker
        tracker = ConversationTracker(
            tracking_uri=config.mlflow_tracking_uri,
            mode=config.mlflow_tracking_mode,
        )
    except ImportError:
        print("MLflow not available, tracking disabled")

    # Initialize CarLogAgent (new LLM-powered agent)
    if config.openai_api_key:
        try:
            from .agent import CarLogAgent, AgentConfig

            agent_config = AgentConfig(
                model="gpt-5-mini",  # Best value: 80% of GPT-5 at 10x cheaper
                workspace_path="/app/workspace",
                max_iterations=5,
                execution_timeout=60,
            )

            car_log_agent = CarLogAgent(
                adapters=adapters,
                config=agent_config,
                tracker=tracker,
            )
            print("CarLogAgent initialized successfully (Code Execution with MCP pattern)")
            use_agent_mode = True

        except ImportError as e:
            print(f"Could not initialize CarLogAgent: {e}")
            use_agent_mode = False
    else:
        print("OPENAI_API_KEY not set - using legacy regex mode")
        use_agent_mode = False

    # Initialize legacy chat handler (fallback)
    chat_handler = ChatHandler(adapters=adapters, tracker=tracker)

    # Initialize DSPy (optional, for legacy mode)
    try:
        from .dspy_modules import configure_dspy
        if config.openai_api_key:
            configure_dspy(
                model=config.openai_model,
                api_key=config.openai_api_key,
            )
    except ImportError:
        print("DSPy not available")


async def process_chat(
    message: str,
    history: List[Tuple[str, str]],
) -> Tuple[str, List[Tuple[str, str]], List[str], str]:
    """
    Process chat message and return response.

    Args:
        message: User input
        history: Chat history

    Returns:
        Tuple of (response_text, updated_history, quick_actions, status_text)
    """
    global chat_handler, car_log_agent, use_agent_mode

    if not chat_handler:
        await initialize_app()

    if not message.strip():
        return "", history, ["Help", "List vehicles"], ""

    status_text = ""

    if use_agent_mode and car_log_agent:
        # Use LLM-powered agent with code execution
        try:
            response = await car_log_agent.process_message(message, history)

            # Build status text
            if response.code_blocks:
                status_text = f"Executed {len(response.code_blocks)} code block(s) in {response.iterations} iteration(s)"
                if response.execution_results:
                    successful = sum(1 for r in response.execution_results if r.success)
                    status_text += f" | {successful}/{len(response.execution_results)} successful"

            # Update history
            new_history = history + [(message, response.message)]

            # Get quick actions (complete prompts for auto-send)
            quick_actions = response.quick_actions or [
                "Add a new checkpoint",
                "Check for gaps in my mileage",
                "Generate a monthly report"
            ]

            return "", new_history, quick_actions, status_text

        except Exception as e:
            print(f"Agent error, falling back to legacy: {e}")
            # Fall through to legacy handler

    # Legacy regex-based handler
    response = await chat_handler.process_message(message, history)

    # Update history
    new_history = history + [(message, response.message)]

    # Get quick actions (complete prompts for auto-send)
    quick_actions = response.quick_actions or [
        "Add a new checkpoint",
        "Check for gaps in my mileage",
        "Generate a monthly report"
    ]

    return "", new_history, quick_actions, "Legacy mode"


def handle_quick_action(action: str, history: List[Tuple[str, str]]):
    """Handle quick action button click."""
    # Convert action to message and process
    message = action_to_message(action) if not action.startswith("action_") else action
    return message


# Create Gradio interface
def create_app() -> gr.Blocks:
    """Create the Gradio application with hybrid navigation."""
    global dashboard_view, checkpoints_view, trips_view, reports_view

    # Custom CSS for stat cards and layout
    custom_css = """
    .status-bar { font-size: 0.8em; color: #666; padding: 4px 8px; }
    .agent-mode { background-color: #e8f5e9; border-radius: 4px; }
    .legacy-mode { background-color: #fff3e0; border-radius: 4px; }
    .stat-card { background: #f8f9fa; padding: 16px; border-radius: 8px; text-align: center; }
    .stat-card h3 { margin: 0; color: #666; font-size: 0.9em; }
    .stat-card h1 { margin: 8px 0; color: #333; }
    .nav-active { background-color: var(--primary-500) !important; color: white !important; }
    .hint-text { font-size: 0.85em; color: #666; font-style: italic; }
    .reports-list { max-height: 300px; overflow-y: auto; }
    """

    with gr.Blocks(
        title="Car Log - Mileage Tracker",
        theme=gr.themes.Soft(),
        fill_height=True,
        css=custom_css,
    ) as app:

        # State (will be initialized after vehicle dropdown is created)
        # Quick actions are complete prompts that auto-send on click
        current_actions = gr.State([
            "Add a new checkpoint",
            "Check for gaps in my mileage",
            "Generate a monthly report"
        ])

        # Pre-populate vehicle dropdown
        def get_initial_vehicles():
            """Get initial vehicle list for dropdown."""
            if not adapters.get("car-log-core"):
                print("[DEBUG] get_initial_vehicles: No car-log-core adapter")
                return [], None
            try:
                import asyncio
                async def _fetch():
                    result = await adapters["car-log-core"].call_tool("list_vehicles", {})
                    print(f"[DEBUG] get_initial_vehicles result: {result.success}")
                    if result.success:
                        vehicles = result.data.get("vehicles", [])
                        print(f"[DEBUG] get_initial_vehicles: Found {len(vehicles)} vehicles")
                        choices = []
                        for v in vehicles:
                            name = v.get('name') or f"{v.get('make', '')} {v.get('model', '')}".strip() or 'Unknown'
                            plate = v.get('license_plate', 'N/A')
                            vid = v.get('vehicle_id', '')
                            print(f"[DEBUG] Vehicle: {name} ({plate}) id={vid}")
                            choices.append((f"{name} ({plate})", vid))
                        return choices, choices[0][1] if choices else None
                    return [], None
                return asyncio.run(_fetch())
            except Exception as e:
                print(f"[DEBUG] get_initial_vehicles error: {e}")
                import traceback
                traceback.print_exc()
                return [], None

        initial_choices, initial_value = get_initial_vehicles()

        # Initialize state with the first vehicle if available
        initial_state = ViewState(selected_vehicle_id=initial_value)
        view_state = gr.State(initial_state.to_dict())

        # Header
        with gr.Row():
            gr.Markdown("# Car Log - Slovak Mileage Tracker")
            with gr.Column(scale=1):
                vehicle_dropdown = gr.Dropdown(
                    label="Vehicle",
                    choices=initial_choices,
                    value=initial_value,
                    allow_custom_value=False,
                    interactive=True,
                )
                mode_indicator = gr.Markdown(
                    value="**Mode:** Agent (LLM)" if use_agent_mode else "**Mode:** Legacy",
                    elem_classes=["agent-mode" if use_agent_mode else "legacy-mode"],
                )

        with gr.Row():
            # Sidebar
            with gr.Column(scale=1, min_width=150):
                gr.Markdown("### Navigation")
                btn_dashboard = gr.Button("Dashboard", variant="secondary", size="sm")
                btn_checkpoints = gr.Button("Checkpoints", variant="secondary", size="sm")
                btn_trips = gr.Button("Trips", variant="secondary", size="sm")
                btn_reports = gr.Button("Reports", variant="secondary", size="sm")
                btn_chat = gr.Button("Chat", variant="primary", size="sm")
                gr.Markdown("---")
                btn_settings = gr.Button("Settings", variant="secondary", size="sm")

                # Agent info
                if use_agent_mode:
                    gr.Markdown("""
                    ---
                    ### Agent Info
                    Using **gpt-4o-mini** with Code Execution pattern for 98% token reduction.
                    """)

            # Main content
            with gr.Column(scale=4):
                # ===== DASHBOARD SECTION =====
                with gr.Column(visible=False) as dashboard_section:
                    gr.Markdown("## Dashboard")
                    gr.Markdown("Overview of your vehicle mileage tracking.")

                    with gr.Row():
                        with gr.Column(scale=1):
                            dash_vehicles = gr.Markdown("### Vehicles\n# 0\n*Registered*")
                        with gr.Column(scale=1):
                            dash_checkpoints = gr.Markdown("### Checkpoints\n# 0\n*Recorded*")
                        with gr.Column(scale=1):
                            dash_trips = gr.Markdown("### Trips\n# 0\n*Logged*")

                    with gr.Row():
                        with gr.Column(scale=1):
                            dash_distance = gr.Markdown("### Total Distance\n# 0 km\n*All time*")
                        with gr.Column(scale=1):
                            dash_efficiency = gr.Markdown("### Avg Efficiency\n# - L/100km\n*Fuel usage*")
                        with gr.Column(scale=1):
                            dash_business = gr.Markdown("### Business Trips\n# 0%\n*Of total*")

                    with gr.Row():
                        dash_last_activity = gr.Markdown("**Last Checkpoint:** None recorded")
                        dash_refresh = gr.Button("Refresh Dashboard", size="sm")

                # ===== CHECKPOINTS SECTION =====
                with gr.Column(visible=False) as checkpoints_section:
                    gr.Markdown("## Checkpoints")
                    gr.Markdown("View and filter your vehicle checkpoints.")

                    with gr.Row():
                        cp_type_filter = gr.Dropdown(
                            label="Type", choices=["All", "refuel", "manual"],
                            value="All", scale=1,
                        )
                        cp_date_from = gr.Textbox(label="From Date", placeholder="YYYY-MM-DD", scale=1)
                        cp_date_to = gr.Textbox(label="To Date", placeholder="YYYY-MM-DD", scale=1)
                        cp_refresh = gr.Button("Refresh", size="sm", scale=1)

                    cp_dataframe = gr.Dataframe(
                        headers=["ID", "Date", "Time", "Odometer (km)", "Type", "Fuel (L)", "Fuel Type", "Location"],
                        interactive=False, wrap=True,
                    )
                    gr.Markdown("*Use chat to add new checkpoints.*", elem_classes=["hint-text"])

                # ===== TRIPS SECTION =====
                with gr.Column(visible=False) as trips_section:
                    gr.Markdown("## Trips")
                    gr.Markdown("View your logged trips with Slovak VAT compliance details.")

                    with gr.Row():
                        trip_purpose_filter = gr.Dropdown(
                            label="Purpose", choices=["All", "Business", "Personal"],
                            value="All", scale=1,
                        )
                        trip_date_from = gr.Textbox(label="From Date", placeholder="YYYY-MM-DD", scale=1)
                        trip_date_to = gr.Textbox(label="To Date", placeholder="YYYY-MM-DD", scale=1)
                        trip_refresh = gr.Button("Refresh", size="sm", scale=1)

                    trip_dataframe = gr.Dataframe(
                        headers=["ID", "Date", "From", "To", "Distance (km)", "Driver", "Purpose", "L/100km", "Method"],
                        interactive=False, wrap=True,
                    )
                    with gr.Row():
                        trip_total_distance = gr.Markdown("**Total Distance:** 0 km")
                        trip_avg_efficiency = gr.Markdown("**Avg Efficiency:** - L/100km")

                    gr.Markdown("*Use chat to reconstruct trips from gaps.*", elem_classes=["hint-text"])

                # ===== REPORTS SECTION =====
                with gr.Column(visible=False) as reports_section:
                    gr.Markdown("## Reports")
                    gr.Markdown("Generate and download mileage reports for Slovak VAT compliance.")

                    with gr.Group():
                        gr.Markdown("### Generate New Report")
                        with gr.Row():
                            report_date_from = gr.Textbox(label="From Date", placeholder="YYYY-MM-DD", scale=1)
                            report_date_to = gr.Textbox(label="To Date", placeholder="YYYY-MM-DD", scale=1)
                            report_format = gr.Dropdown(label="Format", choices=["CSV"], value="CSV", scale=1)
                            report_generate = gr.Button("Generate Report", variant="primary", scale=1)
                        report_status = gr.Markdown("")

                    reports_list_md = gr.Markdown("### Available Reports\n\n*No reports found. Generate one above.*")
                    report_refresh = gr.Button("Refresh List", size="sm")

                # ===== CHAT SECTION =====
                with gr.Column(visible=True) as chat_section:
                    chatbot = gr.Chatbot(
                        label="Assistant",
                        height=400,
                        type="tuples",  # Explicit type (tuples for backward compat, messages for OpenAI-style)
                        allow_tags=False,  # Explicit setting for Gradio 6.0 compatibility
                        avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=car"),
                    )

                    # Execution status bar
                    status_bar = gr.Markdown(value="", elem_classes=["status-bar"])

                    # Quick actions
                    with gr.Row():
                        btn_action1 = gr.Button("Add a new checkpoint", size="sm", variant="secondary")
                        btn_action2 = gr.Button("Check for gaps in my mileage", size="sm", variant="secondary")
                        btn_action3 = gr.Button("Generate a monthly report", size="sm", variant="secondary")

                # ===== CHAT INPUT (Always visible) =====
                with gr.Row():
                    msg_input = gr.Textbox(
                        label="Message",
                        placeholder="Type a message or click a quick action...",
                        scale=9,
                        show_label=False,
                    )
                    send_btn = gr.Button("Send", scale=1, variant="primary")

        # Welcome message
        if use_agent_mode:
            initial_message = """Welcome to Car Log - your Slovak tax-compliant mileage tracker!

**Agent Mode Active** - I use AI to understand your requests and execute operations efficiently.

I can help you:
- **Track checkpoints** from fuel receipts (scan QR codes, fetch e-Kasa data)
- **Reconstruct trips** between checkpoints using GPS-based template matching
- **Validate trips** for Slovak VAT Act 2025 compliance
- **Generate reports** for tax purposes (CSV format)

Use the **navigation buttons** to view data, or just describe what you need!"""
        else:
            initial_message = """Welcome to Car Log - your Slovak tax-compliant mileage tracker!

Use the **navigation buttons** to browse your data:
- **Dashboard** - Overview stats
- **Checkpoints** - Fuel stops and manual entries
- **Trips** - Logged journeys
- **Reports** - Generate tax-compliant reports

Or type a command in the chat below!"""

        chatbot.value = [("", initial_message)]

        # ===== EVENT HANDLERS =====

        # Navigation handlers
        async def nav_to_dashboard(state_dict):
            state = ViewState.from_dict(state_dict)
            state.active_section = "dashboard"

            # Fetch dashboard stats
            if dashboard_view:
                stats = await dashboard_view.fetch_stats(state.selected_vehicle_id)
                distance_str = f"{stats.total_distance_km:,.0f} km"
                eff_str = f"{stats.avg_efficiency:.1f} L/100km" if stats.avg_efficiency > 0 else "- L/100km"
                business_str = f"{stats.business_trip_pct:.0f}%"
                last_cp = f"**Last Checkpoint:** {stats.last_checkpoint_date}" if stats.last_checkpoint_date else "**Last Checkpoint:** None"
            else:
                stats = None
                distance_str, eff_str, business_str, last_cp = "0 km", "- L/100km", "0%", "**Last Checkpoint:** None"

            vis = get_visibility_updates("dashboard")
            return (
                state.to_dict(),
                gr.update(visible=vis[0]),  # dashboard
                gr.update(visible=vis[1]),  # checkpoints
                gr.update(visible=vis[2]),  # trips
                gr.update(visible=vis[3]),  # reports
                gr.update(visible=vis[4]),  # chat
                f"### Vehicles\n# {stats.vehicle_count if stats else 0}\n*Registered*",
                f"### Checkpoints\n# {stats.checkpoint_count if stats else 0}\n*Recorded*",
                f"### Trips\n# {stats.trip_count if stats else 0}\n*Logged*",
                f"### Total Distance\n# {distance_str}\n*All time*",
                f"### Avg Efficiency\n# {eff_str}\n*Fuel usage*",
                f"### Business Trips\n# {business_str}\n*Of total*",
                last_cp,
            )

        async def nav_to_checkpoints(state_dict):
            state = ViewState.from_dict(state_dict)
            state.active_section = "checkpoints"

            # Fetch checkpoints data
            df = None
            if checkpoints_view:
                df = await checkpoints_view.fetch_data(vehicle_id=state.selected_vehicle_id)

            vis = get_visibility_updates("checkpoints")
            return (
                state.to_dict(),
                gr.update(visible=vis[0]),
                gr.update(visible=vis[1]),
                gr.update(visible=vis[2]),
                gr.update(visible=vis[3]),
                gr.update(visible=vis[4]),
                df,
            )

        async def nav_to_trips(state_dict):
            state = ViewState.from_dict(state_dict)
            state.active_section = "trips"

            # Fetch trips data
            df = None
            total_md = "**Total Distance:** 0 km"
            eff_md = "**Avg Efficiency:** - L/100km"
            if trips_view:
                df, total_md, eff_md = await refresh_trips(
                    trips_view, state.selected_vehicle_id, "All", "", ""
                )

            vis = get_visibility_updates("trips")
            return (
                state.to_dict(),
                gr.update(visible=vis[0]),
                gr.update(visible=vis[1]),
                gr.update(visible=vis[2]),
                gr.update(visible=vis[3]),
                gr.update(visible=vis[4]),
                df,
                total_md,
                eff_md,
            )

        async def nav_to_reports(state_dict):
            state = ViewState.from_dict(state_dict)
            state.active_section = "reports"

            # Get reports list
            reports_md = "### Available Reports\n\n*No reports found.*"
            if reports_view:
                reports_md, _ = refresh_reports_list(reports_view)

            vis = get_visibility_updates("reports")
            return (
                state.to_dict(),
                gr.update(visible=vis[0]),
                gr.update(visible=vis[1]),
                gr.update(visible=vis[2]),
                gr.update(visible=vis[3]),
                gr.update(visible=vis[4]),
                reports_md,
            )

        def nav_to_chat(state_dict):
            state = ViewState.from_dict(state_dict)
            state.active_section = "chat"
            vis = get_visibility_updates("chat")
            return (
                state.to_dict(),
                gr.update(visible=vis[0]),
                gr.update(visible=vis[1]),
                gr.update(visible=vis[2]),
                gr.update(visible=vis[3]),
                gr.update(visible=vis[4]),
            )

        # Chat handlers
        async def on_send(message, history):
            response_msg, new_history, actions, status = await process_chat(message, history)
            # Return complete prompts for quick action buttons
            return (
                response_msg,
                new_history,
                actions[0] if len(actions) > 0 else "Add a new checkpoint",
                actions[1] if len(actions) > 1 else "Check for gaps in my mileage",
                actions[2] if len(actions) > 2 else "Generate a monthly report",
                status,
            )

        def on_action_click(action_text):
            """Return the action text to be used as message."""
            return action_text

        # Filter refresh handlers
        async def on_cp_refresh(state_dict, type_filter, date_from, date_to):
            state = ViewState.from_dict(state_dict)
            if checkpoints_view:
                return await refresh_checkpoints(
                    checkpoints_view, state.selected_vehicle_id,
                    type_filter, date_from, date_to
                )
            return None

        async def on_trip_refresh(state_dict, purpose_filter, date_from, date_to):
            state = ViewState.from_dict(state_dict)
            if trips_view:
                return await refresh_trips(
                    trips_view, state.selected_vehicle_id,
                    purpose_filter, date_from, date_to
                )
            return None, "**Total Distance:** 0 km", "**Avg Efficiency:** - L/100km"

        # Report generation (via chat)
        def on_report_generate(date_from, date_to):
            cmd = "Generate report"
            if date_from:
                cmd += f" from {date_from}"
            if date_to:
                cmd += f" to {date_to}"
            return cmd

        # ===== BIND EVENTS =====

        # Vehicle dropdown change handler
        def on_vehicle_change(vehicle_id, state_dict):
            """Update state when vehicle is selected."""
            state = ViewState.from_dict(state_dict)
            state.selected_vehicle_id = vehicle_id
            print(f"[DEBUG] Vehicle changed to: {vehicle_id}")
            return state.to_dict()

        vehicle_dropdown.change(
            on_vehicle_change,
            inputs=[vehicle_dropdown, view_state],
            outputs=[view_state],
        )

        # Navigation buttons
        btn_dashboard.click(
            nav_to_dashboard,
            inputs=[view_state],
            outputs=[
                view_state,
                dashboard_section, checkpoints_section, trips_section, reports_section, chat_section,
                dash_vehicles, dash_checkpoints, dash_trips,
                dash_distance, dash_efficiency, dash_business, dash_last_activity,
            ],
        )

        btn_checkpoints.click(
            nav_to_checkpoints,
            inputs=[view_state],
            outputs=[
                view_state,
                dashboard_section, checkpoints_section, trips_section, reports_section, chat_section,
                cp_dataframe,
            ],
        )

        btn_trips.click(
            nav_to_trips,
            inputs=[view_state],
            outputs=[
                view_state,
                dashboard_section, checkpoints_section, trips_section, reports_section, chat_section,
                trip_dataframe, trip_total_distance, trip_avg_efficiency,
            ],
        )

        btn_reports.click(
            nav_to_reports,
            inputs=[view_state],
            outputs=[
                view_state,
                dashboard_section, checkpoints_section, trips_section, reports_section, chat_section,
                reports_list_md,
            ],
        )

        btn_chat.click(
            nav_to_chat,
            inputs=[view_state],
            outputs=[
                view_state,
                dashboard_section, checkpoints_section, trips_section, reports_section, chat_section,
            ],
        )

        # Dashboard refresh
        dash_refresh.click(
            nav_to_dashboard,
            inputs=[view_state],
            outputs=[
                view_state,
                dashboard_section, checkpoints_section, trips_section, reports_section, chat_section,
                dash_vehicles, dash_checkpoints, dash_trips,
                dash_distance, dash_efficiency, dash_business, dash_last_activity,
            ],
        )

        # Checkpoints refresh
        cp_refresh.click(
            on_cp_refresh,
            inputs=[view_state, cp_type_filter, cp_date_from, cp_date_to],
            outputs=[cp_dataframe],
        )

        # Trips refresh
        trip_refresh.click(
            on_trip_refresh,
            inputs=[view_state, trip_purpose_filter, trip_date_from, trip_date_to],
            outputs=[trip_dataframe, trip_total_distance, trip_avg_efficiency],
        )

        # Reports refresh
        report_refresh.click(
            nav_to_reports,
            inputs=[view_state],
            outputs=[
                view_state,
                dashboard_section, checkpoints_section, trips_section, reports_section, chat_section,
                reports_list_md,
            ],
        )

        # Report generate (sends to chat)
        report_generate.click(
            on_report_generate,
            inputs=[report_date_from, report_date_to],
            outputs=[msg_input],
        )

        # Chat send button
        send_btn.click(
            on_send,
            inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot, btn_action1, btn_action2, btn_action3, status_bar],
        )

        # Chat enter key
        msg_input.submit(
            on_send,
            inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot, btn_action1, btn_action2, btn_action3, status_bar],
        )

        # Quick action buttons - auto-send on click (no need to click Send)
        btn_action1.click(
            on_action_click, inputs=[btn_action1], outputs=[msg_input]
        ).then(
            on_send, inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot, btn_action1, btn_action2, btn_action3, status_bar]
        )
        btn_action2.click(
            on_action_click, inputs=[btn_action2], outputs=[msg_input]
        ).then(
            on_send, inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot, btn_action1, btn_action2, btn_action3, status_bar]
        )
        btn_action3.click(
            on_action_click, inputs=[btn_action3], outputs=[msg_input]
        ).then(
            on_send, inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot, btn_action1, btn_action2, btn_action3, status_bar]
        )

    return app


def main():
    """Main entry point."""
    print("[STARTUP] Car Log application starting...")
    import sys
    print(f"[STARTUP] Python: {sys.version}", flush=True)
    print(f"[STARTUP] DATA_PATH: {os.environ.get('DATA_PATH', 'not set')}", flush=True)

    # Run initialization
    asyncio.run(initialize_app())

    # Create and launch app
    app = create_app()

    config = get_config()
    app.launch(
        server_name=config.server_host,
        server_port=config.server_port,
        share=config.share,
    )


if __name__ == "__main__":
    main()
