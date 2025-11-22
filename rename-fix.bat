@echo off
REM Quick fix to rename mcp-servers to mcp_servers in existing deployment
REM This fixes the ModuleNotFoundError without redeploying

echo ========================================
echo   Quick Fix: Rename mcp-servers Directory
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
echo.

if exist "%DEPLOY_DIR%\mcp_servers" (
    echo Directory already named correctly: mcp_servers
    echo No action needed.
    echo.
    echo Running config regeneration instead...
    call fix-config.bat
    exit /b 0
)

if not exist "%DEPLOY_DIR%\mcp-servers" (
    echo ERROR: Neither mcp-servers nor mcp_servers found
    echo Please redeploy using install.bat
    pause
    exit /b 1
)

echo Renaming mcp-servers to mcp_servers...
ren "%DEPLOY_DIR%\mcp-servers" mcp_servers

if errorlevel 1 (
    echo ERROR: Failed to rename directory
    pause
    exit /b 1
)

echo OK - Directory renamed
echo.

echo Regenerating configuration file...
call fix-config.bat

echo.
echo ========================================
echo   RENAME COMPLETE!
echo ========================================
echo.
echo Next steps shown by fix-config.bat above.
echo.
