@echo off
REM Test deployment script - DRY RUN
echo ========================================
echo   Testing Windows Deployment (DRY RUN)
echo ========================================
echo.

echo This will show you what the deployment script will do:
echo.
echo [1/7] Check prerequisites...
where python >nul 2>&1 && echo   OK - Python found || echo   ERROR - Python NOT found
where node >nul 2>&1 && echo   OK - Node.js found || echo   ERROR - Node.js NOT found
echo.

echo [2/7] Would create directory:
echo   %USERPROFILE%\.car-log-deployment\
echo.

echo [3/7] Would copy:
echo   mcp-servers\ → %USERPROFILE%\.car-log-deployment\mcp-servers\
echo.

echo [4/7] Would copy:
echo   docker\requirements.txt → %USERPROFILE%\.car-log-deployment\requirements.txt
echo.

echo [5/7] Would install Python dependencies:
echo   pip install -r requirements.txt
echo.

echo [6/7] Would install Node.js dependencies:
echo   cd mcp-servers\geo-routing
echo   npm install
echo.

echo [7/7] Would generate config:
echo   %USERPROFILE%\.car-log-deployment\claude_desktop_config.json
echo.

echo ========================================
echo   Ready to run actual deployment?
echo ========================================
echo.
echo To run the REAL deployment:
echo   deployment\scripts\deploy-windows.bat
echo.
pause
