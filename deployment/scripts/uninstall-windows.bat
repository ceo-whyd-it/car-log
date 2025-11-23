@echo off
REM Car Log - Uninstall Script (Windows)
REM Removes Car Log MCP servers deployment

echo ========================================
echo   Car Log - Uninstall
echo ========================================
echo.

set DEPLOY_DIR=%USERPROFILE%\.car-log-deployment

if not exist "%DEPLOY_DIR%" (
    echo Car Log deployment not found.
    echo Location checked: %DEPLOY_DIR%
    echo Nothing to uninstall.
    pause
    exit /b 0
)

echo Deployment found: %DEPLOY_DIR%
echo.
echo WARNING: This will permanently delete:
echo   - All MCP server code
echo   - All your data (vehicles, checkpoints, trips, templates, reports)
echo   - Configuration files
echo.
echo Data location: %DEPLOY_DIR%\data
echo.

set /p confirm="Are you sure you want to uninstall? (yes/no): "

if /i not "%confirm%"=="yes" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo [1/3] Creating backup of data folder...
if exist "%DEPLOY_DIR%\data" (
    set BACKUP_DIR=%USERPROFILE%\car-log-data-backup-%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%
    xcopy /E /I /Y "%DEPLOY_DIR%\data" "%BACKUP_DIR%" >nul
    echo OK - Backup created: %BACKUP_DIR%
) else (
    echo No data folder found, skipping backup
)
echo.

echo [2/3] Removing deployment directory...
rmdir /s /q "%DEPLOY_DIR%"
echo OK - Deployment removed
echo.

echo [3/3] Next steps...
echo.
echo MANUAL CLEANUP REQUIRED:
echo.
echo 1. Remove Car Log servers from Claude Desktop config:
echo    Location: %APPDATA%\Claude\claude_desktop_config.json
echo.
echo    Delete these server entries:
echo      - car-log-core
echo      - trip-reconstructor
echo      - validation
echo      - ekasa-api
echo      - dashboard-ocr
echo      - report-generator
echo      - geo-routing
echo.
echo 2. Restart Claude Desktop
echo.
echo 3. (Optional) Delete data backup if no longer needed:
if exist "%BACKUP_DIR%" (
    echo    %BACKUP_DIR%
)
echo.
echo ========================================
echo   UNINSTALL COMPLETE
echo ========================================
pause
