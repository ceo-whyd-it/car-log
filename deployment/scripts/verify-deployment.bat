@echo off
REM Car Log - Deployment Verification Script
REM Checks if deployment was successful

echo ========================================
echo   Car Log - Deployment Verification
echo ========================================
echo.

set DEPLOY_DIR=%USERPROFILE%\.car-log-deployment
set ERRORS=0

echo Checking deployment at: %DEPLOY_DIR%
echo.

REM Check deployment directory exists
echo [1/10] Checking deployment directory...
if exist "%DEPLOY_DIR%" (
    echo   OK - Deployment directory exists
) else (
    echo   ERROR - Deployment directory NOT found
    set /a ERRORS+=1
)
echo.

REM Check MCP servers copied
echo [2/10] Checking MCP servers...
if exist "%DEPLOY_DIR%\mcp_servers\car_log_core" (
    echo   OK - car-log-core found
) else (
    echo   ERROR - car-log-core NOT found
    set /a ERRORS+=1
)

if exist "%DEPLOY_DIR%\mcp_servers\trip_reconstructor" (
    echo   OK - trip-reconstructor found
) else (
    echo   ERROR - trip-reconstructor NOT found
    set /a ERRORS+=1
)

if exist "%DEPLOY_DIR%\mcp_servers\geo-routing" (
    echo   OK - geo-routing found
) else (
    echo   ERROR - geo-routing NOT found
    set /a ERRORS+=1
)
echo.

REM Check data directories
echo [3/10] Checking data directories...
if exist "%DEPLOY_DIR%\data\vehicles" (
    echo   OK - vehicles/ directory exists
) else (
    echo   ERROR - vehicles/ directory NOT found
    set /a ERRORS+=1
)

if exist "%DEPLOY_DIR%\data\checkpoints" (
    echo   OK - checkpoints/ directory exists
) else (
    echo   ERROR - checkpoints/ directory NOT found
    set /a ERRORS+=1
)

if exist "%DEPLOY_DIR%\data\trips" (
    echo   OK - trips/ directory exists
) else (
    echo   ERROR - trips/ directory NOT found
    set /a ERRORS+=1
)
echo.

REM Check requirements.txt
echo [4/10] Checking requirements.txt...
if exist "%DEPLOY_DIR%\requirements.txt" (
    echo   OK - requirements.txt found
) else (
    echo   ERROR - requirements.txt NOT found
    set /a ERRORS+=1
)
echo.

REM Check Python dependencies
echo [5/10] Checking Python dependencies...
cd /d "%DEPLOY_DIR%"
python -c "import mcp; print('   OK - mcp installed')" 2>nul || (
    echo   ERROR - mcp NOT installed
    set /a ERRORS+=1
)
python -c "import pillow; print('   OK - pillow installed')" 2>nul || (
    echo   ERROR - pillow NOT installed
    set /a ERRORS+=1
)
python -c "import requests; print('   OK - requests installed')" 2>nul || (
    echo   ERROR - requests NOT installed
    set /a ERRORS+=1
)
echo.

REM Check Node.js dependencies
echo [6/10] Checking Node.js dependencies...
if exist "%DEPLOY_DIR%\mcp_servers\geo-routing\node_modules" (
    echo   OK - node_modules found
) else (
    echo   ERROR - node_modules NOT found
    set /a ERRORS+=1
)
echo.

REM Check generated config
echo [7/10] Checking generated config...
if exist "%DEPLOY_DIR%\claude_desktop_config.json" (
    echo   OK - claude_desktop_config.json found
) else (
    echo   ERROR - claude_desktop_config.json NOT found
    set /a ERRORS+=1
)
echo.

REM Check Python can import MCP servers
echo [8/10] Testing Python imports...
cd /d "%DEPLOY_DIR%"
python -c "from mcp_servers import car_log_core; print('   OK - car_log_core imports')" 2>nul || (
    echo   ERROR - car_log_core import failed
    set /a ERRORS+=1
)
python -c "from mcp_servers import trip_reconstructor; print('   OK - trip_reconstructor imports')" 2>nul || (
    echo   ERROR - trip_reconstructor import failed
    set /a ERRORS+=1
)
echo.

REM Check disk space usage
echo [9/10] Checking disk space...
for /f "tokens=3" %%a in ('dir "%DEPLOY_DIR%" ^| find "bytes free"') do set FREE_SPACE=%%a
echo   Deployment directory created
echo   Location: %DEPLOY_DIR%
echo.

REM Summary
echo [10/10] Summary...
echo.
if %ERRORS%==0 (
    echo ========================================
    echo   VERIFICATION PASSED - ALL OK!
    echo ========================================
    echo.
    echo Deployment is complete and functional.
    echo.
    echo NEXT STEPS:
    echo   1. Run merge-config script:
    echo      deployment\scripts\merge-config-windows.bat
    echo.
    echo   2. Or manually merge config:
    echo      From: %DEPLOY_DIR%\claude_desktop_config.json
    echo      To:   %APPDATA%\Claude\claude_desktop_config.json
    echo.
    echo   3. Restart Claude Desktop
    echo.
    exit /b 0
) else (
    echo ========================================
    echo   VERIFICATION FAILED - %ERRORS% ERROR(S)
    echo ========================================
    echo.
    echo Please re-run deployment script:
    echo   deployment\scripts\deploy-windows.bat
    echo.
    exit /b 1
)
