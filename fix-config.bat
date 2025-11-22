@echo off
REM Quick fix script to regenerate config with proper paths
REM Run this if you're seeing MCP server errors in Claude Desktop

echo ========================================
echo   Fixing Claude Desktop Config
echo ========================================
echo.

set DEPLOY_DIR=%USERPROFILE%\.car-log-deployment

if not exist "%DEPLOY_DIR%" (
    echo ERROR: Deployment not found at: %DEPLOY_DIR%
    echo Please run install.bat first
    pause
    exit /b 1
)

echo Deployment found: %DEPLOY_DIR%
echo Regenerating configuration file...
echo.

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
echo             "args": [os.path.join^(deploy_dir, "mcp_servers", "geo-routing", "index.js"^)],
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

echo.
echo ========================================
echo   CONFIG FIXED!
echo ========================================
echo.
echo Updated config file: %DEPLOY_DIR%\claude_desktop_config.json
echo.
echo NEXT STEPS:
echo.
echo 1. Run the merge script:
echo    deployment\scripts\merge-config-windows.bat
echo.
echo 2. Restart Claude Desktop
echo.
echo 3. Check that MCP servers load without errors
echo.
pause
