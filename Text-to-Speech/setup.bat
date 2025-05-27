@echo off
setlocal enabledelayedexpansion

echo Setting up Text-to-Speech application...
echo.

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if we're in a nested directory structure
set "CURRENT_DIR=%CD%"
echo Current directory: %CURRENT_DIR%
if "%CURRENT_DIR:~-15%"=="Text-to-Speech" (
    echo WARNING: Detected nested Text-to-Speech directory structure.
    echo Please run this script from the main Text-to-Speech directory.
    pause
    exit /b 1
)

REM Create a log file
set "LOG_FILE=%SCRIPT_DIR%setup_log.txt"
echo Setup started at %date% %time% > "%LOG_FILE%"

REM Check if Python is installed and find a compatible version
echo Checking Python installation and finding compatible version (3.11 or 3.10)...

set "PYTHON_CMD="

REM Try Python 3.11
where python3.11 >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python3.11"
    echo Found Python 3.11.
    goto found_python
)

REM Try Python 3.10
where python3.10 >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python3.10"
    echo Found Python 3.10.
    goto found_python
)

REM Fallback to default python if no specific version found (might still fail with Python 3.13)
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    echo Using default python. This may fail if default is Python 3.13.
    goto found_python
)

REM If no python found at all
echo ERROR: Compatible Python version (3.10 or 3.11) not found or default python not in PATH!
echo Please install Python 3.10 or 3.11 from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo Compatible Python not found >> "%LOG_FILE%"
pause
exit /b 1

:found_python

REM Remove existing virtual environment if it exists
if exist ".venv" (
    echo Removing existing virtual environment...
    rmdir /s /q ".venv"
    if errorlevel 1 (
        echo Failed to remove existing virtual environment
        echo Failed to remove .venv >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)

REM Create virtual environment using the found python command
echo Creating virtual environment using !PYTHON_CMD!...
!PYTHON_CMD! -m venv .venv
if errorlevel 1 (
    echo Failed to create virtual environment
    echo Failed to create .venv >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate
if errorlevel 1 (
    echo Failed to activate virtual environment
    echo Failed to activate .venv >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
!PYTHON_CMD! -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip
    echo Failed to upgrade pip >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Install setuptools and wheel
echo Installing setuptools and wheel...
pip install setuptools wheel
if errorlevel 1 (
    echo Failed to install setuptools and wheel
    echo Failed to install setuptools and wheel >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Install PyTorch first (CPU version to avoid CUDA issues)
echo Installing PyTorch...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
    echo Failed to install PyTorch
    echo Failed to install PyTorch >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Install audio dependencies
echo Installing audio dependencies...
pip install PyAudio
pip install sounddevice
pip install soundfile
if errorlevel 1 (
    echo Failed to install audio dependencies
    echo Failed to install audio dependencies >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Install all required packages from requirements.txt
echo Installing required packages from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install required packages
    echo Failed to install requirements.txt packages >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Install additional system dependencies
echo Installing additional system dependencies...
pip install psutil
pip install pyautogui
if errorlevel 1 (
    echo Failed to install system dependencies
    echo Failed to install system dependencies >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Install OpenCV for image processing
echo Installing OpenCV...
pip install opencv-python
if errorlevel 1 (
    echo Failed to install OpenCV
    echo Failed to install OpenCV >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Check for FFmpeg
echo Checking for FFmpeg...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo FFmpeg not found. Downloading and setting up FFmpeg...

    REM Create ffmpeg directory if it doesn't exist
    if not exist "ffmpeg" mkdir ffmpeg

    REM Download FFmpeg
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile 'ffmpeg.zip'}"
    if errorlevel 1 (
        echo Failed to download FFmpeg
        echo Failed to download FFmpeg >> "%LOG_FILE%"
        pause
        exit /b 1
    )

    REM Extract FFmpeg
    powershell -Command "& {Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg' -Force}"
    if errorlevel 1 (
        echo Failed to extract FFmpeg
        echo Failed to extract FFmpeg >> "%LOG_FILE%"
        pause
        exit /b 1
    )

    REM Move FFmpeg files to the correct location
    move "ffmpeg\ffmpeg-master-latest-win64-gpl\bin\*" "ffmpeg\"
    rmdir /s /q "ffmpeg\ffmpeg-master-latest-win64-gpl"
    del "ffmpeg.zip"
)

REM Check for Tesseract-OCR folder
if not exist "Tesseract-OCR" (
    echo.
    echo WARNING: Tesseract-OCR folder not found!
    echo Please download Tesseract-OCR from: https://github.com/UB-Mannheim/tesseract/wiki
    echo Extract the Tesseract-OCR folder to this directory.
    echo.
    echo The application will try to use system-installed Tesseract if available,
    echo but it's recommended to have the Tesseract-OCR folder in this directory.
    echo Tesseract-OCR folder not found >> "%LOG_FILE%"
)

REM Create a configuration file for the application
echo Creating configuration file...
(
echo {
echo   "app_dir": "%SCRIPT_DIR%",
echo   "ffmpeg_path": "%SCRIPT_DIR%ffmpeg",
echo   "tesseract_path": "%SCRIPT_DIR%Tesseract-OCR",
echo   "venv_path": "%SCRIPT_DIR%.venv"
echo }
) > "app_config.json"

echo Setup completed successfully! >> "%LOG_FILE%"
echo.
echo Setup completed successfully!
echo.
echo To run the application, double-click on 'run.bat'
echo.
pause 