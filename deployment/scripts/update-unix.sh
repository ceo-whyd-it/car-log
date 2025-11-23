#!/bin/bash
# Car Log - Update Script (macOS/Linux)
# Updates MCP servers to latest version while preserving data

set -e

echo "========================================"
echo "  Car Log - Update"
echo "========================================"
echo ""

DEPLOY_DIR="$HOME/.car-log-deployment"

if [ ! -d "$DEPLOY_DIR" ]; then
    echo "ERROR: Car Log deployment not found."
    echo "Location: $DEPLOY_DIR"
    echo "Please run deploy-macos.sh or deploy-linux.sh first"
    exit 1
fi

echo "Deployment found: $DEPLOY_DIR"
echo ""
echo "This will update MCP servers to the latest version."
echo "Your data will NOT be deleted."
echo ""

read -p "Continue with update? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Update cancelled."
    exit 0
fi

echo ""
echo "[1/5] Backing up current deployment..."
BACKUP_DIR="$DEPLOY_DIR-backup-$(date +%Y%m%d-%H%M%S)"
cp -r "$DEPLOY_DIR/mcp-servers" "$BACKUP_DIR/"
echo "OK - Backup created: $BACKUP_DIR"
echo ""

echo "[2/5] Copying updated MCP server code..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

rm -rf "$DEPLOY_DIR/mcp-servers"
cp -r "$PROJECT_ROOT/mcp-servers" "$DEPLOY_DIR/"
echo "OK - Code updated"
echo ""

echo "[3/5] Copying updated requirements..."
cp "$PROJECT_ROOT/docker/requirements.txt" "$DEPLOY_DIR/"
echo "OK - Requirements updated"
echo ""

echo "[4/5] Updating Python dependencies..."
cd "$DEPLOY_DIR"
python3 -m pip install --upgrade pip --quiet --user
python3 -m pip install -r requirements.txt --upgrade --quiet --user
echo "OK - Python dependencies updated"
echo ""

echo "[5/5] Updating Node.js dependencies..."
cd "$DEPLOY_DIR/mcp-servers/geo-routing"
npm update --silent
echo "OK - Node.js dependencies updated"
echo ""

echo "========================================"
echo "  UPDATE COMPLETE"
echo "========================================"
echo ""
echo "MCP servers updated to latest version."
echo "Data preserved in: $DEPLOY_DIR/data"
echo ""
echo "NEXT STEP: Restart Claude Desktop"
echo ""
echo "If you experience issues, restore from backup:"
echo "  $BACKUP_DIR"
echo ""
