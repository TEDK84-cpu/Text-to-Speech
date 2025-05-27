@echo off
setlocal enabledelayedexpansion

echo Starting Text-to-Speech application...
echo Current directory: %CD%

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
echo Script directory: %SCRIPT_DIR%

REM Create logs directory if it doesn't exist
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"

REM Set up logging
set "LOG_FILE=%SCRIPT_DIR%logs\run_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "LOG_FILE=!LOG_FILE: =0!"

REM Function to log messages
call :log "Starting application..."

REM Check if Python script exists
if not exist "%SCRIPT_DIR%Text-to-Speech.py" (
    call :log "Error: Text-to-Speech.py not found!"
    call :log "Looking in: %SCRIPT_DIR%"
    echo Please run setup.bat first to install the application.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "%SCRIPT_DIR%.venv\Scripts\activate.bat" (
    call :log "Error: Virtual environment not found!"
    echo Please run setup.bat first to install the application.
    pause
    exit /b 1
)

REM Set FFmpeg path
set "FFMPEG_PATH=%SCRIPT_DIR%ffmpeg"
set "PATH=%FFMPEG_PATH%;%PATH%"
call :log "FFmpeg path set to: %FFMPEG_PATH%"

REM Verify FFmpeg exists
if not exist "%FFMPEG_PATH%\ffmpeg.exe" (
    call :log "Error: FFmpeg not found!"
    echo Please run setup.bat first to install the application.
    pause
    exit /b 1
)

REM Activate virtual environment
call :log "Activating virtual environment..."
call "%SCRIPT_DIR%.venv\Scripts\activate.bat"
if errorlevel 1 (
    call :log "Failed to activate virtual environment!"
    echo Please run setup.bat first to install the application.
    pause
    exit /b 1
)

REM Set environment variables for the Python script
set "PYTHONPATH=%SCRIPT_DIR%"
set "FFMPEG_BINARY=%FFMPEG_PATH%\ffmpeg.exe"
set "FFPROBE_BINARY=%FFMPEG_PATH%\ffprobe.exe"
set "TESSERACT_PATH=%SCRIPT_DIR%Tesseract-OCR\tesseract.exe"

REM Verify Tesseract exists
if not exist "%TESSERACT_PATH%" (
    call :log "Warning: Tesseract not found in %TESSERACT_PATH%"
    call :log "The application will try to use system-installed Tesseract if available"
)

REM Run the Python script using the virtual environment's python
call :log "Running Python script..."
python "%SCRIPT_DIR%Text-to-Speech.py"

if errorlevel 1 (
    call :log "Python script failed!"
    call :log "Error code: %errorlevel%"
    pause
    exit /b 1
)

call :log "Application completed successfully"
pause
exit /b 0

:log
echo %~1
echo %date% %time% - %~1 >> "%LOG_FILE%"
exit /b 0 