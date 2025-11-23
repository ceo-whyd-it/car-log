@echo off
REM Car Log - Update Script (Windows)
REM Updates MCP servers to latest version while preserving data

echo ========================================
echo   Car Log - Update
echo ========================================
echo.

set DEPLOY_DIR=%USERPROFILE%\.car-log-deployment

if not exist "%DEPLOY_DIR%" (
    echo ERROR: Car Log deployment not found.
    echo Location: %DEPLOY_DIR%
    echo Please run deploy-windows.bat first
    pause
    exit /b 1
)

echo Deployment found: %DEPLOY_DIR%
echo.
echo This will update MCP servers to the latest version.
echo Your data will NOT be deleted.
echo.

set /p confirm="Continue with update? (yes/no): "

if /i not "%confirm%"=="yes" (
    echo Update cancelled.
    pause
    exit /b 0
)

echo.
echo [1/5] Backing up current deployment...
set BACKUP_DIR=%DEPLOY_DIR%-backup-%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%
xcopy /E /I /Y "%DEPLOY_DIR%\mcp_servers" "%BACKUP_DIR%\mcp_servers" >nul
echo OK - Backup created: %BACKUP_DIR%
echo.

echo [2/5] Copying updated MCP server code...
xcopy /E /I /Y "%~dp0..\..\mcp-servers" "%DEPLOY_DIR%\mcp_servers" >nul
echo OK - Code updated
echo.

echo [3/5] Copying updated requirements...
copy /Y "%~dp0..\..\docker\requirements.txt" "%DEPLOY_DIR%\requirements.txt" >nul
echo OK - Requirements updated
echo.

echo [4/5] Updating Python dependencies...
cd /d "%DEPLOY_DIR%"
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --upgrade --quiet
echo OK - Python dependencies updated
echo.

echo [5/5] Updating Node.js dependencies...
cd /d "%DEPLOY_DIR%\mcp_servers\geo-routing"
call npm update --silent
echo OK - Node.js dependencies updated
echo.

echo ========================================
echo   UPDATE COMPLETE
echo ========================================
echo.
echo MCP servers updated to latest version.
echo Data preserved in: %DEPLOY_DIR%\data
echo.
echo NEXT STEP: Restart Claude Desktop
echo.
echo If you experience issues, restore from backup:
echo   %BACKUP_DIR%
echo.
pause
