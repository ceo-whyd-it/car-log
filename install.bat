@echo off
REM Car Log - Quick Install Launcher
REM This is a convenience script to run the full deployment

echo.
echo Starting Car Log deployment...
echo.

call deployment\scripts\deploy-windows.bat

if errorlevel 1 (
    echo.
    echo Deployment encountered errors.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Running verification...
echo ========================================
echo.

call deployment\scripts\verify-deployment.bat

pause
