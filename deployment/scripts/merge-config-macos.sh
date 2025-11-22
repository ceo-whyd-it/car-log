#!/bin/bash
# Car Log - Merge Configuration Helper (macOS)
# Automatically merges Car Log MCP servers into Claude Desktop config

set -e

echo "========================================"
echo "  Car Log - Config Merge Helper"
echo "========================================"
echo ""

DEPLOY_DIR="$HOME/.car-log-deployment"
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
GENERATED_CONFIG="$DEPLOY_DIR/claude_desktop_config.json"

# Check if deployment exists
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "ERROR: Deployment not found at $DEPLOY_DIR"
    echo "Please run deploy-macos.sh first"
    exit 1
fi

# Check if generated config exists
if [ ! -f "$GENERATED_CONFIG" ]; then
    echo "ERROR: Generated config not found at $GENERATED_CONFIG"
    echo "Please run deploy-macos.sh first"
    exit 1
fi

echo "Deployment found: $DEPLOY_DIR"
echo "Generated config: $GENERATED_CONFIG"
echo "Claude config: $CLAUDE_CONFIG"
echo ""

# Check if Claude Desktop config exists
if [ ! -f "$CLAUDE_CONFIG" ]; then
    echo "Claude Desktop config not found."
    echo "Creating new config file..."

    # Create Claude directory if needed
    mkdir -p "$HOME/Library/Application Support/Claude"

    # Copy generated config as-is
    cp "$GENERATED_CONFIG" "$CLAUDE_CONFIG"

    echo "OK - Config file created"
    echo ""
    echo "NEXT STEP: Restart Claude Desktop"
    exit 0
fi

echo "Claude Desktop config already exists."
echo ""
echo "This script will help you merge the Car Log servers."
echo ""
echo "OPTIONS:"
echo "  1. Backup current config and replace with Car Log config"
echo "  2. Open both files for manual merge"
echo "  3. Show merge instructions"
echo "  4. Cancel"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "Creating backup..."
        cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup"
        echo "OK - Backup created: $CLAUDE_CONFIG.backup"
        echo ""
        echo "Replacing config..."
        cp "$GENERATED_CONFIG" "$CLAUDE_CONFIG"
        echo "OK - Config replaced"
        echo ""
        echo "WARNING: This replaced your entire Claude Desktop config."
        echo "If you had other MCP servers, restore from backup:"
        echo "  $CLAUDE_CONFIG.backup"
        echo ""
        echo "NEXT STEP: Restart Claude Desktop"
        ;;

    2)
        echo ""
        echo "Opening both files..."
        if command -v code &> /dev/null; then
            code "$CLAUDE_CONFIG"
            code "$GENERATED_CONFIG"
            echo "Files opened in VS Code"
        elif command -v nano &> /dev/null; then
            echo "Opening Claude config in nano..."
            echo "Press Ctrl+X when done, then you'll see the generated config"
            nano "$CLAUDE_CONFIG"
            echo ""
            echo "Opening generated config in nano..."
            nano "$GENERATED_CONFIG"
        else
            echo "No suitable editor found. Opening with default app..."
            open -e "$CLAUDE_CONFIG"
            open -e "$GENERATED_CONFIG"
        fi
        echo ""
        echo "MANUAL MERGE INSTRUCTIONS:"
        echo ""
        echo "1. In your Claude config, find the 'mcpServers' section"
        echo "2. Copy the Car Log servers from the generated config"
        echo "3. Paste them into your Claude config"
        echo "4. Save the Claude config file"
        echo "5. Restart Claude Desktop"
        ;;

    3)
        echo ""
        echo "MANUAL MERGE INSTRUCTIONS:"
        echo "========================================"
        echo ""
        echo "1. Open Claude Desktop config:"
        echo "   $CLAUDE_CONFIG"
        echo ""
        echo "2. Open generated config:"
        echo "   $GENERATED_CONFIG"
        echo ""
        echo "3. If your Claude config looks like this:"
        echo "   {"
        echo "     \"mcpServers\": {"
        echo "       \"existing-server\": { ... }"
        echo "     }"
        echo "   }"
        echo ""
        echo "4. Add Car Log servers after existing servers:"
        echo "   {"
        echo "     \"mcpServers\": {"
        echo "       \"existing-server\": { ... },"
        echo ""
        echo "       \"car-log-core\": { ... },"
        echo "       \"trip-reconstructor\": { ... },"
        echo "       (... other Car Log servers)"
        echo "     }"
        echo "   }"
        echo ""
        echo "5. Save and restart Claude Desktop"
        ;;

    4)
        echo ""
        echo "Merge cancelled."
        exit 0
        ;;

    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
