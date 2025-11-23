@echo off
REM Car Log - Merge Configuration Helper (Windows)
REM Automatically merges Car Log MCP servers into Claude Desktop config

echo ========================================
echo   Car Log - Config Merge Helper
echo ========================================
echo.

set DEPLOY_DIR=%USERPROFILE%\.car-log-deployment
set CLAUDE_CONFIG=%APPDATA%\Claude\claude_desktop_config.json
set GENERATED_CONFIG=%DEPLOY_DIR%\claude_desktop_config.json

REM Check if deployment exists
if not exist "%DEPLOY_DIR%" (
    echo ERROR: Deployment not found at %DEPLOY_DIR%
    echo Please run deploy-windows.bat first
    pause
    exit /b 1
)

REM Check if generated config exists
if not exist "%GENERATED_CONFIG%" (
    echo ERROR: Generated config not found at %GENERATED_CONFIG%
    echo Please run deploy-windows.bat first
    pause
    exit /b 1
)

echo Deployment found: %DEPLOY_DIR%
echo Generated config: %GENERATED_CONFIG%
echo Claude config: %CLAUDE_CONFIG%
echo.

REM Check if Claude Desktop config exists
if not exist "%CLAUDE_CONFIG%" (
    echo Claude Desktop config not found.
    echo Creating new config file...

    REM Create Claude directory if needed
    if not exist "%APPDATA%\Claude" mkdir "%APPDATA%\Claude"

    REM Copy generated config as-is
    copy /Y "%GENERATED_CONFIG%" "%CLAUDE_CONFIG%" >nul

    echo OK - Config file created
    echo.
    echo NEXT STEP: Restart Claude Desktop
    pause
    exit /b 0
)

echo Claude Desktop config already exists.
echo.
echo This script will help you merge the Car Log servers.
echo.
echo OPTIONS:
echo   1. Backup current config and replace with Car Log config
echo   2. Open both files for manual merge
echo   3. Show merge instructions
echo   4. Cancel
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto backup_replace
if "%choice%"=="2" goto open_files
if "%choice%"=="3" goto show_instructions
if "%choice%"=="4" goto cancel

echo Invalid choice
pause
exit /b 1

:backup_replace
echo.
echo Creating backup...
copy /Y "%CLAUDE_CONFIG%" "%CLAUDE_CONFIG%.backup" >nul
echo OK - Backup created: %CLAUDE_CONFIG%.backup
echo.
echo Replacing config...
copy /Y "%GENERATED_CONFIG%" "%CLAUDE_CONFIG%" >nul
echo OK - Config replaced
echo.
echo WARNING: This replaced your entire Claude Desktop config.
echo If you had other MCP servers, restore from backup:
echo   %CLAUDE_CONFIG%.backup
echo.
echo NEXT STEP: Restart Claude Desktop
pause
exit /b 0

:open_files
echo.
echo Opening both files in Notepad...
start notepad "%CLAUDE_CONFIG%"
timeout /t 1 >nul
start notepad "%GENERATED_CONFIG%"
echo.
echo MANUAL MERGE INSTRUCTIONS:
echo.
echo 1. In your Claude config (first window), find the "mcpServers" section
echo 2. Copy the Car Log servers from the generated config (second window)
echo 3. Paste them into your Claude config
echo 4. Save the Claude config file
echo 5. Close both Notepad windows
echo 6. Restart Claude Desktop
echo.
pause
exit /b 0

:show_instructions
echo.
echo MANUAL MERGE INSTRUCTIONS:
echo ========================================
echo.
echo 1. Open Claude Desktop config:
echo    %CLAUDE_CONFIG%
echo.
echo 2. Open generated config:
echo    %GENERATED_CONFIG%
echo.
echo 3. If your Claude config looks like this:
echo    {
echo      "mcpServers": {
echo        "existing-server": { ... }
echo      }
echo    }
echo.
echo 4. Add Car Log servers after existing servers:
echo    {
echo      "mcpServers": {
echo        "existing-server": { ... },
echo
echo        "car-log-core": { ... },
echo        "trip-reconstructor": { ... },
echo        (... other Car Log servers)
echo      }
echo    }
echo.
echo 5. Save and restart Claude Desktop
echo.
pause
exit /b 0

:cancel
echo.
echo Merge cancelled.
pause
exit /b 0
