# Car Log MCP Servers - Deployment Guide

This directory contains deployment scripts to install Car Log MCP servers for use with Claude Desktop.

## Overview

The deployment scripts will:
1. ✅ Create a deployment directory outside the git repository (`~/.car-log-deployment`)
2. ✅ Copy all MCP server code
3. ✅ Install Python and Node.js dependencies
4. ✅ Generate a Claude Desktop configuration file
5. ✅ Provide step-by-step instructions to integrate with Claude Desktop

## Prerequisites

### All Platforms
- **Claude Desktop** installed ([download here](https://claude.ai/download))
- Internet connection (for installing dependencies)

### Platform-Specific Requirements

#### Windows
- **Python 3.11+** ([download](https://www.python.org/downloads/))
- **Node.js 18+** ([download](https://nodejs.org/))

#### macOS
- **Python 3.11+** (install with Homebrew: `brew install python@3.11`)
- **Node.js 18+** (install with Homebrew: `brew install node@18`)

#### Linux
- **Python 3.11+**
  - Ubuntu/Debian: `sudo apt install python3.11 python3-pip`
  - Fedora: `sudo dnf install python3.11 python3-pip`
  - Arch: `sudo pacman -S python python-pip`
- **Node.js 18+**
  - Ubuntu/Debian: See [NodeSource setup](https://github.com/nodesource/distributions)
  - Fedora: `sudo dnf install nodejs`
  - Arch: `sudo pacman -S nodejs npm`

## Quick Start

### Windows

1. Open Command Prompt or PowerShell as Administrator
2. Navigate to the project directory:
   ```cmd
   cd path\to\car-log
   ```
3. Run the deployment script:
   ```cmd
   deployment\scripts\deploy-windows.bat
   ```
4. Follow the on-screen instructions

### macOS

1. Open Terminal
2. Navigate to the project directory:
   ```bash
   cd ~/path/to/car-log
   ```
3. Run the deployment script:
   ```bash
   ./deployment/scripts/deploy-macos.sh
   ```
4. Follow the on-screen instructions

### Linux

1. Open Terminal
2. Navigate to the project directory:
   ```bash
   cd ~/path/to/car-log
   ```
3. Run the deployment script:
   ```bash
   ./deployment/scripts/deploy-linux.sh
   ```
4. Follow the on-screen instructions

## What Gets Deployed

### Deployment Directory Structure
```
~/.car-log-deployment/
├── mcp-servers/              # MCP server source code
│   ├── car_log_core/
│   ├── trip_reconstructor/
│   ├── validation/
│   ├── ekasa_api/
│   ├── dashboard_ocr/
│   ├── report_generator/
│   └── geo-routing/          # Node.js server
├── data/                     # Runtime data (created empty)
│   ├── vehicles/
│   ├── checkpoints/
│   ├── trips/
│   ├── templates/
│   └── reports/
├── requirements.txt          # Python dependencies
└── claude_desktop_config.json # Generated config
```

### MCP Servers Included

| Server | Description | Language |
|--------|-------------|----------|
| **car-log-core** | CRUD operations for vehicles, checkpoints, templates | Python |
| **trip-reconstructor** | Template matching and trip reconstruction | Python |
| **validation** | 4 validation algorithms for data quality | Python |
| **ekasa-api** | Slovak e-Kasa receipt processing | Python |
| **dashboard-ocr** | EXIF extraction from dashboard photos | Python |
| **report-generator** | CSV/PDF report generation | Python |
| **geo-routing** | Geocoding and route calculation (OpenStreetMap) | Node.js |

## Integrating with Claude Desktop

After running the deployment script, you need to merge the configuration with Claude Desktop:

### Option A: Automatic Merge (Coming Soon)
```bash
# macOS/Linux
./deployment/scripts/merge-config-macos.sh  # or merge-config-linux.sh

# Windows
deployment\scripts\merge-config-windows.bat
```

### Option B: Manual Merge (Current Method)

1. **Locate Claude Desktop config file:**
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

2. **Open the generated config:**
   - Located at: `~/.car-log-deployment/claude_desktop_config.json`

3. **Merge the configurations:**
   - If Claude Desktop config is **empty** or **doesn't exist**, copy entire file
   - If you **have existing MCP servers**, merge the `mcpServers` section:

   ```json
   {
     "mcpServers": {
       "existing-server": { ... },  // Keep your existing servers

       // Add Car Log servers from generated config:
       "car-log-core": { ... },
       "trip-reconstructor": { ... },
       "validation": { ... },
       "ekasa-api": { ... },
       "dashboard-ocr": { ... },
       "report-generator": { ... },
       "geo-routing": { ... }
     }
   }
   ```

4. **Save the file**

5. **Restart Claude Desktop**

## Verification

After restarting Claude Desktop, verify the servers are loaded:

1. Open a new conversation in Claude Desktop
2. Type: "What MCP tools do you have available?"
3. Look for Car Log servers in the response

Expected tools:
- `create_vehicle`, `list_vehicles`, `get_vehicle`, `update_vehicle`, `delete_vehicle`
- `create_checkpoint`, `list_checkpoints`, `analyze_gap`
- `create_template`, `list_templates`, `match_templates`
- `validate_trip`
- `fetch_receipt`, `scan_qr_from_pdf`
- `extract_metadata`, `check_photo_quality`
- `generate_report`
- `geocode_address`, `calculate_route`, `reverse_geocode`

## Configuration

### Optional: Set Anthropic API Key

The `dashboard-ocr` server uses Claude Vision for OCR. To enable it:

1. Open the generated config:
   - `~/.car-log-deployment/claude_desktop_config.json`

2. Find the `dashboard-ocr` section

3. Replace the placeholder:
   ```json
   "ANTHROPIC_API_KEY": "your_anthropic_api_key_here"
   ```
   with your actual API key:
   ```json
   "ANTHROPIC_API_KEY": "sk-ant-..."
   ```

4. Copy the updated config to Claude Desktop (repeat merge process)

5. Restart Claude Desktop

## Troubleshooting

### "Python not found"
- Install Python 3.11+ from https://www.python.org/
- On Windows, check "Add Python to PATH" during installation

### "Node.js not found"
- Install Node.js 18+ from https://nodejs.org/
- Ensure `node` and `npm` are in your PATH

### "Permission denied" (macOS/Linux)
- Make scripts executable:
  ```bash
  chmod +x deployment/scripts/*.sh
  ```

### MCP servers not appearing in Claude Desktop
1. Check Claude Desktop logs:
   - **Windows:** `%APPDATA%\Claude\logs\`
   - **macOS:** `~/Library/Logs/Claude/`
   - **Linux:** `~/.config/Claude/logs/`

2. Verify config file syntax (must be valid JSON)

3. Ensure paths in config are absolute (not relative)

4. Restart Claude Desktop completely (quit and reopen)

### "ModuleNotFoundError" when using tools
- Re-run deployment script to reinstall dependencies
- Check Python version: `python --version` (must be 3.11+)

## Updating

To update to the latest version:

1. Pull latest changes from git:
   ```bash
   git pull origin main
   ```

2. Re-run the deployment script:
   - Windows: `deployment\scripts\deploy-windows.bat`
   - macOS: `./deployment/scripts/deploy-macos.sh`
   - Linux: `./deployment/scripts/deploy-linux.sh`

3. Restart Claude Desktop

## Uninstalling

To remove Car Log MCP servers:

1. Remove from Claude Desktop config:
   - Delete the Car Log server entries from `claude_desktop_config.json`

2. Delete deployment directory:
   - **Windows:** `rmdir /s %USERPROFILE%\.car-log-deployment`
   - **macOS/Linux:** `rm -rf ~/.car-log-deployment`

3. Restart Claude Desktop

## Data Location

All runtime data is stored in:
- `~/.car-log-deployment/data/`

This includes:
- Vehicles
- Checkpoints
- Trips
- Templates
- Reports

**Backup this directory regularly** to prevent data loss.

## Support

For issues or questions:
1. Check [GitHub Issues](https://github.com/your-repo/car-log/issues)
2. Read the main project [README](../README.md)
3. Review the [CLAUDE.md](../CLAUDE.md) implementation guide

## License

See [LICENSE](../LICENSE) in the project root.
