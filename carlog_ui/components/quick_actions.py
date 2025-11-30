"""
Quick action buttons component for Gradio UI.

Provides contextual action buttons that change based on current state.
"""

from __future__ import annotations
import gradio as gr
from typing import List, Tuple, Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from gradio.layouts import Row


# Context-based quick actions
QUICK_ACTIONS = {
    "default": [
        ("+ Add Checkpoint", "add_checkpoint"),
        ("Check for Gaps", "detect_gaps"),
        ("Generate Report", "generate_report"),
    ],
    "gap_detected": [
        ("Reconstruct Trips", "reconstruct_trips"),
        ("Accept All", "accept_trips"),
        ("View Details", "view_details"),
        ("Reject", "reject_trips"),
    ],
    "proposals_ready": [
        ("Accept All", "accept_trips"),
        ("Edit Trips", "edit_trips"),
        ("Add Template", "add_template"),
        ("Reject", "reject_trips"),
    ],
    "checkpoint_list": [
        ("+ New Checkpoint", "add_checkpoint"),
        ("Reconstruct Trips", "reconstruct_trips"),
        ("Export CSV", "generate_report"),
    ],
    "after_edit": [
        ("Save Changes", "save_changes"),
        ("Undo", "undo"),
        ("Validate", "validate"),
    ],
    "error": [
        ("Retry", "retry"),
        ("Manual Entry", "manual_entry"),
        ("Get Help", "help"),
    ],
}


def get_actions_for_context(context: str = "default") -> List[Tuple[str, str]]:
    """
    Get quick actions for a given context.

    Args:
        context: Current UI context

    Returns:
        List of (label, action_id) tuples
    """
    return QUICK_ACTIONS.get(context, QUICK_ACTIONS["default"])


def create_quick_actions(
    context: str = "default",
    on_click: Callable[[str], None] = None,
) -> Tuple[Any, List[Tuple[Any, str]]]:
    """
    Create quick action buttons row.

    Args:
        context: Initial context for actions
        on_click: Callback when button clicked (receives action_id)

    Returns:
        Gradio Row with action buttons
    """
    actions = get_actions_for_context(context)

    with gr.Row() as row:
        buttons = []
        for label, action_id in actions[:5]:  # Max 5 buttons
            btn = gr.Button(
                label,
                size="sm",
                variant="secondary",
            )
            buttons.append((btn, action_id))

    return row, buttons


def update_quick_actions(context: str) -> List[gr.Button]:
    """
    Get updated button configurations for a context.

    Args:
        context: New context

    Returns:
        List of gr.Button.update() calls
    """
    actions = get_actions_for_context(context)

    updates = []
    for i in range(5):
        if i < len(actions):
            label, _ = actions[i]
            updates.append(gr.Button(value=label, visible=True))
        else:
            updates.append(gr.Button(visible=False))

    return updates


def action_to_message(action_id: str) -> str:
    """
    Convert action ID to chat message.

    Args:
        action_id: Action identifier

    Returns:
        Message to send to chat handler
    """
    action_messages = {
        "add_checkpoint": "Add checkpoint",
        "detect_gaps": "Check for gaps",
        "generate_report": "Generate report",
        "reconstruct_trips": "Reconstruct trips",
        "accept_trips": "Accept all trips",
        "reject_trips": "Reject trips",
        "view_details": "Show details",
        "edit_trips": "Edit trips",
        "add_template": "Add template",
        "save_changes": "Save changes",
        "undo": "Undo",
        "validate": "Validate",
        "retry": "Retry",
        "manual_entry": "Manual entry",
        "help": "Help",
    }
    return action_messages.get(action_id, action_id)
