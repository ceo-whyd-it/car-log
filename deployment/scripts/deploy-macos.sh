#!/bin/bash
# Car Log MCP Servers - macOS Deployment Script
# This script deploys MCP servers to a folder outside the git repository
# for use with Claude Desktop on macOS

set -e  # Exit on error

echo "========================================"
echo "  Car Log MCP Servers - macOS Deploy"
echo "========================================"
echo ""

# Set deployment directory (outside git repo)
DEPLOY_DIR="$HOME/.car-log-deployment"
echo "Deployment directory: $DEPLOY_DIR"
echo ""

# Check prerequisites
echo "[1/7] Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found! Please install Python 3.11+"
    echo "Install with Homebrew: brew install python@3.11"
    echo "Or download from: https://www.python.org/downloads/"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found! Please install Node.js 18+"
    echo "Install with Homebrew: brew install node@18"
    echo "Or download from: https://nodejs.org/"
    exit 1
fi

python3 --version
node --version
echo "OK - Prerequisites found"
echo ""

# Create deployment directory
echo "[2/7] Creating deployment directory..."
mkdir -p "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR/data"/{vehicles,checkpoints,trips,templates,reports}
echo "OK - Directories created"
echo ""

# Copy MCP server source code
echo "[3/7] Copying MCP server code..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cp -r "$PROJECT_ROOT/mcp-servers" "$DEPLOY_DIR/"
echo "OK - MCP servers copied"
echo ""

# Copy requirements.txt
echo "[4/7] Copying requirements..."
cp "$PROJECT_ROOT/docker/requirements.txt" "$DEPLOY_DIR/"
echo "OK - Requirements copied"
echo ""

# Install Python dependencies
echo "[5/7] Installing Python dependencies..."
echo "This may take a few minutes..."
cd "$DEPLOY_DIR"
python3 -m pip install --upgrade pip --quiet
python3 -m pip install -r requirements.txt --quiet
echo "OK - Python dependencies installed"
echo ""

# Install Node.js dependencies for geo-routing
echo "[6/7] Installing Node.js dependencies..."
cd "$DEPLOY_DIR/mcp-servers/geo-routing"
npm install --silent
echo "OK - Node.js dependencies installed"
echo ""

# Generate Claude Desktop config
echo "[7/7] Generating Claude Desktop configuration..."
cd "$DEPLOY_DIR"
cat > claude_desktop_config.json <<EOF
{
  "mcpServers": {
    "car-log-core": {
      "command": "python3",
      "args": ["-m", "mcp_servers.car_log_core"],
      "cwd": "$DEPLOY_DIR",
      "env": {
        "DATA_PATH": "$DEPLOY_DIR/data",
        "USE_ATOMIC_WRITES": "true"
      }
    },
    "trip-reconstructor": {
      "command": "python3",
      "args": ["-m", "mcp_servers.trip_reconstructor"],
      "cwd": "$DEPLOY_DIR",
      "env": {
        "GPS_WEIGHT": "0.7",
        "ADDRESS_WEIGHT": "0.3",
        "CONFIDENCE_THRESHOLD": "70"
      }
    },
    "validation": {
      "command": "python3",
      "args": ["-m", "mcp_servers.validation"],
      "cwd": "$DEPLOY_DIR",
      "env": {
        "DISTANCE_VARIANCE_PERCENT": "10",
        "CONSUMPTION_VARIANCE_PERCENT": "15",
        "DIESEL_MIN_L_PER_100KM": "5",
        "DIESEL_MAX_L_PER_100KM": "15"
      }
    },
    "ekasa-api": {
      "command": "python3",
      "args": ["-m", "mcp_servers.ekasa_api"],
      "cwd": "$DEPLOY_DIR",
      "env": {
        "EKASA_API_URL": "https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt",
        "MCP_TIMEOUT_SECONDS": "60"
      }
    },
    "dashboard-ocr": {
      "command": "python3",
      "args": ["-m", "mcp_servers.dashboard_ocr"],
      "cwd": "$DEPLOY_DIR",
      "env": {
        "ANTHROPIC_API_KEY": "your_anthropic_api_key_here"
      }
    },
    "report-generator": {
      "command": "python3",
      "args": ["-m", "mcp_servers.report_generator"],
      "cwd": "$DEPLOY_DIR",
      "env": {
        "DATA_PATH": "$DEPLOY_DIR/data"
      }
    },
    "geo-routing": {
      "command": "node",
      "args": ["$DEPLOY_DIR/mcp-servers/geo-routing/index.js"],
      "env": {
        "OSRM_BASE_URL": "https://router.project-osrm.org",
        "NOMINATIM_BASE_URL": "https://nominatim.openstreetmap.org",
        "CACHE_TTL_HOURS": "24"
      }
    }
  }
}
EOF
echo "OK - Configuration generated"
echo ""

# Display completion message
echo "========================================"
echo "  DEPLOYMENT COMPLETE!"
echo "========================================"
echo ""
echo "Deployment location: $DEPLOY_DIR"
echo "Data directory: $DEPLOY_DIR/data"
echo "Config file: $DEPLOY_DIR/claude_desktop_config.json"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Open Claude Desktop configuration file:"
echo "   Location: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
echo "2. Copy the contents from:"
echo "   $DEPLOY_DIR/claude_desktop_config.json"
echo ""
echo "3. Option A - Auto-merge (recommended):"
echo "   ./deployment/scripts/merge-config-macos.sh"
echo ""
echo "   Option B - Manual merge:"
echo "   Open both files and merge the 'mcpServers' sections"
echo ""
echo "4. Restart Claude Desktop"
echo ""
echo "5. Verify MCP servers are loaded in Claude Desktop"
echo ""
echo "OPTIONAL: Set your Anthropic API key for dashboard OCR:"
echo "   Edit: $DEPLOY_DIR/claude_desktop_config.json"
echo "   Find: \"ANTHROPIC_API_KEY\": \"your_anthropic_api_key_here\""
echo "   Replace with your actual API key"
echo ""
