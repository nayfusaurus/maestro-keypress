@echo off
setlocal

:: Change to the directory where this script is located
cd /d "%~dp0"

echo ========================================
echo Building Maestro for Windows
echo ========================================
echo.

:: Check if Python is installed
python --version
if errorlevel 1 (
    echo.
    echo ERROR: Python not found!
    echo Please install from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    goto :end
)

:: Check if pyinstaller is installed
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing dependencies...
    pip install mido pynput pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        goto :end
    )
)

echo.
echo Building executable...
pyinstaller Maestro.spec --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: Build failed.
    goto :end
)

echo.
if exist dist\Maestro.exe (
    echo ========================================
    echo SUCCESS! Executable created at:
    echo   %cd%\dist\Maestro.exe
    echo ========================================
) else (
    echo ERROR: Build completed but exe not found.
)

:end
echo.
echo Press any key to close...
pause >nul
