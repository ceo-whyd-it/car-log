"""
Reports View - Report generation and download list.

Shows available reports and provides generation options.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import os
import gradio as gr


class ReportsView:
    """
    Reports list and generation view component.

    Displays available reports and provides CSV generation options.
    """

    def __init__(self, adapters: Dict[str, Any], reports_dir: Optional[str] = None):
        """
        Initialize ReportsView.

        Args:
            adapters: Dictionary of MCP adapters (needs "report-generator")
            reports_dir: Directory where reports are stored
        """
        self.report_generator = adapters.get("report-generator")
        self.reports_dir = reports_dir or os.path.expanduser("~/Documents/MileageLog/data/reports")

    def list_reports(self) -> List[Dict[str, Any]]:
        """
        List available report files.

        Returns:
            List of report info dicts with name, date, size, path
        """
        reports = []
        reports_path = Path(self.reports_dir)

        if not reports_path.exists():
            return reports

        try:
            for file in reports_path.glob("*.csv"):
                stat = file.stat()
                reports.append({
                    "name": file.name,
                    "date": stat.st_mtime,
                    "size_kb": stat.st_size / 1024,
                    "path": str(file),
                })

            # Sort by date descending (newest first)
            reports.sort(key=lambda x: x["date"], reverse=True)

        except Exception as e:
            print(f"Error listing reports: {e}")

        return reports

    def _format_reports_markdown(self, reports: List[Dict[str, Any]]) -> str:
        """Format reports list as markdown."""
        if not reports:
            return """
### No Reports Found

Generate your first report using the chat:
- Type "Generate report" or "Generate CSV report"
- Specify date range if needed
"""

        lines = ["### Available Reports", ""]
        for report in reports[:10]:  # Show last 10
            from datetime import datetime
            date_str = datetime.fromtimestamp(report["date"]).strftime("%Y-%m-%d %H:%M")
            size_str = f"{report['size_kb']:.1f} KB"
            lines.append(f"- **{report['name']}** - {date_str} ({size_str})")

        if len(reports) > 10:
            lines.append(f"\n*...and {len(reports) - 10} more reports*")

        return "\n".join(lines)

    def create_component(self) -> tuple:
        """
        Create Gradio components for reports view.

        Returns:
            Tuple of (container, components)
        """
        reports = self.list_reports()

        with gr.Column(visible=False) as container:
            gr.Markdown("## Reports")
            gr.Markdown("Generate and download mileage reports for Slovak VAT compliance.")

            # Report generation section
            with gr.Group():
                gr.Markdown("### Generate New Report")
                with gr.Row():
                    date_from = gr.Textbox(
                        label="From Date",
                        placeholder="YYYY-MM-DD (optional)",
                        scale=1,
                    )
                    date_to = gr.Textbox(
                        label="To Date",
                        placeholder="YYYY-MM-DD (optional)",
                        scale=1,
                    )
                    report_format = gr.Dropdown(
                        label="Format",
                        choices=["CSV"],
                        value="CSV",
                        scale=1,
                    )
                    generate_btn = gr.Button("Generate Report", variant="primary", scale=1)

                generation_status = gr.Markdown("")

            # Reports list
            reports_list = gr.Markdown(
                self._format_reports_markdown(reports),
                elem_classes=["reports-list"],
            )

            # Refresh button
            with gr.Row():
                refresh_btn = gr.Button("Refresh List", size="sm")

            # Download section
            if reports:
                gr.Markdown("### Download")
                download_dropdown = gr.Dropdown(
                    label="Select Report",
                    choices=[r["name"] for r in reports],
                    value=reports[0]["name"] if reports else None,
                )
                download_file = gr.File(
                    label="Download",
                    visible=bool(reports),
                )
            else:
                download_dropdown = gr.Dropdown(
                    label="Select Report",
                    choices=[],
                    visible=False,
                )
                download_file = gr.File(
                    label="Download",
                    visible=False,
                )

            # Compliance info
            gr.Markdown("""
---
**Slovak VAT Act 2025 Compliance:**
- Reports include VIN, driver name, dates, and L/100km format
- Business vs Personal trip categorization
- All required fields for tax deduction
            """)

        components = (
            date_from, date_to, report_format, generate_btn,
            generation_status, reports_list, refresh_btn,
            download_dropdown, download_file
        )
        return container, components


def refresh_reports_list(view: ReportsView) -> tuple:
    """
    Refresh the reports list.

    Args:
        view: ReportsView instance

    Returns:
        Tuple of (reports_markdown, dropdown_choices, dropdown_value)
    """
    reports = view.list_reports()
    markdown = view._format_reports_markdown(reports)
    choices = [r["name"] for r in reports]
    value = choices[0] if choices else None

    return markdown, gr.update(choices=choices, value=value)


def get_report_file(view: ReportsView, report_name: str) -> Optional[str]:
    """
    Get file path for download.

    Args:
        view: ReportsView instance
        report_name: Name of report file

    Returns:
        File path or None
    """
    if not report_name:
        return None

    reports = view.list_reports()
    for report in reports:
        if report["name"] == report_name:
            return report["path"]
    return None
