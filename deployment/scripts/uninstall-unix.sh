#!/bin/bash
# Car Log - Uninstall Script (macOS/Linux)
# Removes Car Log MCP servers deployment

set -e

echo "========================================"
echo "  Car Log - Uninstall"
echo "========================================"
echo ""

DEPLOY_DIR="$HOME/.car-log-deployment"

if [ ! -d "$DEPLOY_DIR" ]; then
    echo "Car Log deployment not found."
    echo "Location checked: $DEPLOY_DIR"
    echo "Nothing to uninstall."
    exit 0
fi

echo "Deployment found: $DEPLOY_DIR"
echo ""
echo "WARNING: This will permanently delete:"
echo "  - All MCP server code"
echo "  - All your data (vehicles, checkpoints, trips, templates, reports)"
echo "  - Configuration files"
echo ""
echo "Data location: $DEPLOY_DIR/data"
echo ""

read -p "Are you sure you want to uninstall? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo "[1/3] Creating backup of data folder..."
if [ -d "$DEPLOY_DIR/data" ]; then
    BACKUP_DIR="$HOME/car-log-data-backup-$(date +%Y%m%d-%H%M%S)"
    cp -r "$DEPLOY_DIR/data" "$BACKUP_DIR"
    echo "OK - Backup created: $BACKUP_DIR"
else
    echo "No data folder found, skipping backup"
fi
echo ""

echo "[2/3] Removing deployment directory..."
rm -rf "$DEPLOY_DIR"
echo "OK - Deployment removed"
echo ""

echo "[3/3] Next steps..."
echo ""
echo "MANUAL CLEANUP REQUIRED:"
echo ""

# Detect OS for config path
if [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
else
    CONFIG_PATH="$HOME/.config/Claude/claude_desktop_config.json"
fi

echo "1. Remove Car Log servers from Claude Desktop config:"
echo "   Location: $CONFIG_PATH"
echo ""
echo "   Delete these server entries:"
echo "     - car-log-core"
echo "     - trip-reconstructor"
echo "     - validation"
echo "     - ekasa-api"
echo "     - dashboard-ocr"
echo "     - report-generator"
echo "     - geo-routing"
echo ""
echo "2. Restart Claude Desktop"
echo ""
if [ -d "$BACKUP_DIR" ]; then
    echo "3. (Optional) Delete data backup if no longer needed:"
    echo "   $BACKUP_DIR"
    echo ""
fi
echo "========================================"
echo "  UNINSTALL COMPLETE"
echo "========================================"
