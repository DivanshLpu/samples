@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo          SMART FILE ORGANIZER - BUILD SCRIPT
echo ============================================================
echo.

where gcc >nul 2>nul
if errorlevel 1 (
    echo [ERROR] GCC was not found in PATH.
    echo.
    echo Install MinGW-w64/GCC and make sure gcc.exe is in PATH.
    echo Then run this file again.
    pause
    exit /b 1
)

echo [1/2] Compiling...
gcc src\main.c -o SmartFileOrganizer.exe -mwindows -Wall -Wextra -O2 -lshell32 -lole32
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo [OK] Build successful.
echo.
echo [2/2] Starting Smart File Organizer...
if not exist data mkdir data
start "Smart File Organizer" "%CD%\SmartFileOrganizer.exe"

endlocal
