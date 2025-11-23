@echo off
REM Diagnostic script to troubleshoot MCP server issues
REM Run this to identify why Claude Desktop is showing errors

echo ========================================
echo   MCP Server Diagnostics
echo ========================================
echo.

set DEPLOY_DIR=%USERPROFILE%\.car-log-deployment

echo [1/8] Checking deployment directory...
if exist "%DEPLOY_DIR%" (
    echo   OK - Found: %DEPLOY_DIR%
) else (
    echo   ERROR - Not found: %DEPLOY_DIR%
    echo   Run install.bat first
    pause
    exit /b 1
)
echo.

echo [2/8] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo   ERROR - Python not found in PATH
    pause
    exit /b 1
) else (
    python --version
    echo   OK - Python found
)
echo.

echo [3/8] Checking Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo   ERROR - Node.js not found in PATH
    pause
    exit /b 1
) else (
    node --version
    echo   OK - Node.js found
)
echo.

echo [4/8] Checking MCP servers directory...
if exist "%DEPLOY_DIR%\mcp-servers" (
    echo   OK - mcp-servers directory exists
    dir /B "%DEPLOY_DIR%\mcp-servers"
) else (
    echo   ERROR - mcp-servers directory not found
)
echo.

echo [5/8] Testing Python can import mcp_servers...
cd /d "%DEPLOY_DIR%"
python -c "import sys; sys.path.insert(0, '.'); import mcp_servers; print('   OK - mcp_servers package found')" 2>nul
if errorlevel 1 (
    echo   ERROR - Cannot import mcp_servers package
    echo.
    echo   Checking package structure:
    dir /B mcp-servers
    echo.
    echo   Checking if __init__.py exists:
    if exist "mcp-servers\__init__.py" (
        echo   Found: mcp-servers\__init__.py
    ) else (
        echo   MISSING: mcp-servers\__init__.py
    )
    if exist "mcp_servers\__init__.py" (
        echo   Found: mcp_servers\__init__.py
    ) else (
        echo   MISSING: mcp_servers\__init__.py
    )
)
echo.

echo [6/8] Checking individual MCP server modules...
cd /d "%DEPLOY_DIR%"

for %%s in (car_log_core trip_reconstructor validation ekasa_api dashboard_ocr report_generator) do (
    if exist "mcp-servers\%%s" (
        echo   Found directory: %%s
        if exist "mcp-servers\%%s\__init__.py" (
            echo     - Has __init__.py
        ) else (
            echo     - MISSING __init__.py
        )
        if exist "mcp-servers\%%s\server.py" (
            echo     - Has server.py
        ) else (
            echo     - MISSING server.py
        )
    ) else (
        echo   MISSING directory: %%s
    )
)
echo.

echo [7/8] Checking generated config file...
if exist "%DEPLOY_DIR%\claude_desktop_config.json" (
    echo   OK - Config file exists
    echo.
    echo   Displaying first 20 lines:
    powershell -Command "Get-Content '%DEPLOY_DIR%\claude_desktop_config.json' | Select-Object -First 20"
) else (
    echo   ERROR - Config file not found
)
echo.

echo [8/8] Checking Claude Desktop config location...
set CLAUDE_CONFIG=%APPDATA%\Claude\claude_desktop_config.json
if exist "%CLAUDE_CONFIG%" (
    echo   OK - Claude Desktop config exists
    echo   Location: %CLAUDE_CONFIG%
    echo.
    echo   Displaying full config:
    type "%CLAUDE_CONFIG%"
) else (
    echo   WARNING - Claude Desktop config not found
    echo   Expected: %CLAUDE_CONFIG%
    echo   You need to merge the config using:
    echo   deployment\scripts\merge-config-windows.bat
)
echo.

echo ========================================
echo   Diagnostics Complete
echo ========================================
echo.
echo If you see errors above, common fixes:
echo.
echo 1. Missing __init__.py files:
echo    - The mcp-servers folder needs to be named mcp_servers
echo    - Run: ren "%DEPLOY_DIR%\mcp-servers" mcp_servers
echo.
echo 2. Python cannot import modules:
echo    - Check PYTHONPATH is not interfering
echo    - Try running from deployment directory
echo.
echo 3. Config not merged:
echo    - Run: deployment\scripts\merge-config-windows.bat
echo.
pause
