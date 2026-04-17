@echo off
setlocal EnableDelayedExpansion

echo =======================================
echo      Pingator Launcher (Windows)
echo =======================================

:: 1. Parameter Reading
set MODE=web
set DETACHED=true
set HEADLESS_FLAG=

for %%A in (%*) do (
    if "%%A"=="--tray" set MODE=tray
    if "%%A"=="--debug" set DETACHED=false
    if "%%A"=="--no-browser" set HEADLESS_FLAG=--server.headless=true
)

:: 2. Virtual Environment (venv) Setup
if not exist "venv\Scripts\python.exe" (
    echo [WARNING] The Python virtual environment ^(venv^) was not found.
    set /p install_venv="Do you want to create the environment and install packages now? (y/n): "
    
    if /I "!install_venv!"=="y" (
        echo Creating virtual environment...
        python -m venv venv
        if errorlevel 1 (
            echo [ERROR] Failed to create venv. Make sure Python 3 is installed and added to PATH.
            pause
            exit /b 1
        )
        echo Installing dependencies...
        venv\Scripts\pip install -r requirements.txt
        echo [SUCCESS] Setup completed!
    ) else (
        echo Installation canceled. Exiting...
        pause
        exit /b 0
    )
)

:: 4. Build Command (Background vs Debug)
if "%MODE%"=="tray" (
    echo Starting Pingator in the System Tray...
    if "%DETACHED%"=="true" (
        set CMD=venv\Scripts\pythonw.exe tray.py
    ) else (
        set CMD=venv\Scripts\python.exe tray.py
    )
) else (
    echo Starting Pingator in Web mode...
    if "%DETACHED%"=="true" (
        set CMD=venv\Scripts\pythonw.exe -m streamlit run app.py --server.address=0.0.0.0 !HEADLESS_FLAG!
    ) else (
        set CMD=venv\Scripts\streamlit.exe run app.py --server.address=0.0.0.0 !HEADLESS_FLAG!
    )
)

:: 5. Execution
if "%DETACHED%"=="true" (
    echo The process has been sent to the background! Closing this terminal in 3 seconds...
    timeout /t 3 >nul
    start "" !CMD!
    exit
) else (
    echo [Debug Mode Activated] Press CTRL+C to stop.
    echo ---------------------------------------------------
    !CMD!
)