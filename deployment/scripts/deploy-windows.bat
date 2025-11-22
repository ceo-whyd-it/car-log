@echo off
REM Car Log MCP Servers - Windows Deployment Script
REM This script deploys MCP servers to a folder outside the git repository
REM for use with Claude Desktop on Windows

echo ========================================
echo   Car Log MCP Servers - Windows Deploy
echo ========================================
echo.

REM Set deployment directory (outside git repo)
set DEPLOY_DIR=%USERPROFILE%\.car-log-deployment
echo Deployment directory: %DEPLOY_DIR%
echo.

REM Check prerequisites
echo [1/7] Checking prerequisites...
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.11+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found! Please install Node.js 18+
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)

python --version
node --version
echo OK - Prerequisites found
echo.

REM Create deployment directory
echo [2/7] Creating deployment directory...
if not exist "%DEPLOY_DIR%" mkdir "%DEPLOY_DIR%"
if not exist "%DEPLOY_DIR%\data" mkdir "%DEPLOY_DIR%\data"
if not exist "%DEPLOY_DIR%\data\vehicles" mkdir "%DEPLOY_DIR%\data\vehicles"
if not exist "%DEPLOY_DIR%\data\checkpoints" mkdir "%DEPLOY_DIR%\data\checkpoints"
if not exist "%DEPLOY_DIR%\data\trips" mkdir "%DEPLOY_DIR%\data\trips"
if not exist "%DEPLOY_DIR%\data\templates" mkdir "%DEPLOY_DIR%\data\templates"
if not exist "%DEPLOY_DIR%\data\reports" mkdir "%DEPLOY_DIR%\data\reports"
echo OK - Directories created
echo.

REM Copy MCP server source code
echo [3/7] Copying MCP server code...
xcopy /E /I /Y "%~dp0..\..\mcp-servers" "%DEPLOY_DIR%\mcp-servers" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy MCP servers
    pause
    exit /b 1
)
echo OK - MCP servers copied
echo.

REM Copy requirements.txt
echo [4/7] Copying requirements...
copy /Y "%~dp0..\..\docker\requirements.txt" "%DEPLOY_DIR%\requirements.txt" >nul
echo OK - Requirements copied
echo.

REM Install Python dependencies
echo [5/7] Installing Python dependencies...
echo This may take a few minutes...
cd /d "%DEPLOY_DIR%"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
echo OK - Python dependencies installed
echo.

REM Install Node.js dependencies for geo-routing
echo [6/7] Installing Node.js dependencies...
cd /d "%DEPLOY_DIR%\mcp-servers\geo-routing"
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies
    pause
    exit /b 1
)
echo OK - Node.js dependencies installed
echo.

REM Generate Claude Desktop config
echo [7/7] Generating Claude Desktop configuration...
cd /d "%DEPLOY_DIR%"

REM Create Python script to generate proper JSON config
(
echo import json
echo import os
echo.
echo deploy_dir = os.environ['DEPLOY_DIR']
echo.
echo config = {
echo     "mcpServers": {
echo         "car-log-core": {
echo             "command": "python",
echo             "args": ["-m", "mcp_servers.car_log_core"],
echo             "cwd": deploy_dir,
echo             "env": {
echo                 "DATA_PATH": os.path.join^(deploy_dir, "data"^),
echo                 "USE_ATOMIC_WRITES": "true"
echo             }
echo         },
echo         "trip-reconstructor": {
echo             "command": "python",
echo             "args": ["-m", "mcp_servers.trip_reconstructor"],
echo             "cwd": deploy_dir,
echo             "env": {
echo                 "GPS_WEIGHT": "0.7",
echo                 "ADDRESS_WEIGHT": "0.3",
echo                 "CONFIDENCE_THRESHOLD": "70"
echo             }
echo         },
echo         "validation": {
echo             "command": "python",
echo             "args": ["-m", "mcp_servers.validation"],
echo             "cwd": deploy_dir,
echo             "env": {
echo                 "DISTANCE_VARIANCE_PERCENT": "10",
echo                 "CONSUMPTION_VARIANCE_PERCENT": "15",
echo                 "DIESEL_MIN_L_PER_100KM": "5",
echo                 "DIESEL_MAX_L_PER_100KM": "15"
echo             }
echo         },
echo         "ekasa-api": {
echo             "command": "python",
echo             "args": ["-m", "mcp_servers.ekasa_api"],
echo             "cwd": deploy_dir,
echo             "env": {
echo                 "EKASA_API_URL": "https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt",
echo                 "MCP_TIMEOUT_SECONDS": "60"
echo             }
echo         },
echo         "dashboard-ocr": {
echo             "command": "python",
echo             "args": ["-m", "mcp_servers.dashboard_ocr"],
echo             "cwd": deploy_dir,
echo             "env": {
echo                 "ANTHROPIC_API_KEY": "your_anthropic_api_key_here"
echo             }
echo         },
echo         "report-generator": {
echo             "command": "python",
echo             "args": ["-m", "mcp_servers.report_generator"],
echo             "cwd": deploy_dir,
echo             "env": {
echo                 "DATA_PATH": os.path.join^(deploy_dir, "data"^)
echo             }
echo         },
echo         "geo-routing": {
echo             "command": "node",
echo             "args": [os.path.join^(deploy_dir, "mcp-servers", "geo-routing", "index.js"^)],
echo             "env": {
echo                 "OSRM_BASE_URL": "https://router.project-osrm.org",
echo                 "NOMINATIM_BASE_URL": "https://nominatim.openstreetmap.org",
echo                 "CACHE_TTL_HOURS": "24"
echo             }
echo         }
echo     }
echo }
echo.
echo with open^('claude_desktop_config.json', 'w'^) as f:
echo     json.dump^(config, f, indent=2^)
) > generate_config.py

REM Run the Python script to generate config
python generate_config.py
del generate_config.py
echo OK - Configuration generated
echo.

REM Display completion message
echo ========================================
echo   DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Deployment location: %DEPLOY_DIR%
echo Data directory: %DEPLOY_DIR%\data
echo Config file: %DEPLOY_DIR%\claude_desktop_config.json
echo.
echo NEXT STEPS:
echo.
echo 1. Open Claude Desktop configuration file:
echo    Location: %%APPDATA%%\Claude\claude_desktop_config.json
echo    Full path: %APPDATA%\Claude\claude_desktop_config.json
echo.
echo 2. Copy the contents from:
echo    %DEPLOY_DIR%\claude_desktop_config.json
echo.
echo 3. Paste into your Claude Desktop config file
echo    (Merge with existing config if you have other MCP servers)
echo.
echo 4. Restart Claude Desktop
echo.
echo 5. Verify MCP servers are loaded in Claude Desktop
echo.
echo OPTIONAL: Set your Anthropic API key for dashboard OCR:
echo    Edit: %DEPLOY_DIR%\claude_desktop_config.json
echo    Find: "ANTHROPIC_API_KEY": "your_anthropic_api_key_here"
echo    Replace with your actual API key
echo.
pause
