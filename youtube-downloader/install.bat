```bat
@echo off
setlocal EnableExtensions

title Downloader
echo ==========================================
echo        EXE + FFmpeg Downloader
echo ==========================================
echo.

REM Create download directory
if not exist "tools" mkdir "tools"

REM ------------------------------------------------
REM 1. Download your EXE file
REM ------------------------------------------------
echo [1/2] Downloading application...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Invoke-WebRequest -Uri 'https://example.com/myapp.exe' -OutFile 'tools\myapp.exe'"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to download the EXE file.
    pause
    exit /b 1
)

echo EXE downloaded successfully.
echo.

REM ------------------------------------------------
REM 2. Download FFmpeg
REM ------------------------------------------------
echo [2/2] Downloading FFmpeg...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'tools\ffmpeg.zip'"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to download FFmpeg.
    pause
    exit /b 1
)

echo FFmpeg downloaded.
echo.

REM ------------------------------------------------
REM 3. Extract FFmpeg
REM ------------------------------------------------
echo Extracting FFmpeg...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Expand-Archive -Path 'tools\ffmpeg.zip' -DestinationPath 'tools\ffmpeg_temp' -Force"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to extract FFmpeg.
    pause
    exit /b 1
)

REM Find extracted FFmpeg directory and move it
for /d %%D in ("tools\ffmpeg_temp\ffmpeg-*") do (
    if exist "%%D\bin\ffmpeg.exe" (
        if exist "tools\ffmpeg" rmdir /s /q "tools\ffmpeg"
        move "%%D" "tools\ffmpeg" >nul
    )
)

REM Remove temporary files
rmdir /s /q "tools\ffmpeg_temp" 2>nul
del /q "tools\ffmpeg.zip" 2>nul

echo.
echo ==========================================
echo             INSTALLATION DONE
echo ==========================================
echo.
echo Application:
echo   tools\myapp.exe
echo.
echo FFmpeg:
echo   tools\ffmpeg\bin\ffmpeg.exe
echo.

REM Test FFmpeg
if exist "tools\ffmpeg\bin\ffmpeg.exe" (
    echo FFmpeg installation verified.
) else (
    echo WARNING: FFmpeg was not found.
)

echo.
pause
```
