@echo off
setlocal

:: Change to the directory where this script is located
cd /d "%~dp0"

echo ========================================
echo Building Maestro for Windows
echo ========================================
echo.

:: Check if uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: uv not found!
    echo Please install from https://docs.astral.sh/uv/
    echo   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    goto :end
)

echo Installing dependencies...
uv sync
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    goto :end
)

echo.
echo Adding pyinstaller...
uv add pyinstaller --dev
if errorlevel 1 (
    echo ERROR: Failed to add pyinstaller.
    goto :end
)

echo.
echo Building executable...
uv run pyinstaller Maestro.spec --noconfirm
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
