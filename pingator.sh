#!/bin/bash

echo "======================================="
echo "     Pingator Launcher (Linux)"
echo "======================================="

# 1. Parameter Reading
MODE="web"
DETACHED="true"
HEADLESS_FLAG=""

for arg in "$@"; do
    if [ "$arg" == "--tray" ]; then MODE="tray"; fi
    if [ "$arg" == "--debug" ]; then DETACHED="false"; fi
    if [ "$arg" == "--no-browser" ]; then HEADLESS_FLAG="--server.headless=true"; fi
done

# 2. Universal System Dependencies Check (Ubuntu/Debian, Fedora, Arch)
MISSING_PKGS=""

# Checks for traceroute
if ! command -v traceroute &> /dev/null; then 
    MISSING_PKGS="traceroute"
fi

# Universal check to see if the Python venv module is available
if ! python3 -c "import venv" &> /dev/null; then
    if command -v apt-get &> /dev/null; then
        MISSING_PKGS="$MISSING_PKGS python3-venv"
    elif command -v pacman &> /dev/null; then
        MISSING_PKGS="$MISSING_PKGS python"
    else
        MISSING_PKGS="$MISSING_PKGS python3"
    fi
fi

if [ -n "$MISSING_PKGS" ]; then
    echo "[WARNING] Missing system packages: $MISSING_PKGS"
    read -r -p "Do you want to install them now? (Requires sudo) (y/n): " install_sys
    
    if [[ "$install_sys" =~ ^[Yy]$ ]]; then
        INSTALL_FAIL=false
        
        # Detects the package manager and installs accordingly
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            # shellcheck disable=SC2086
            if ! sudo apt-get install -y $MISSING_PKGS; then INSTALL_FAIL=true; fi
            
        elif command -v dnf &> /dev/null; then
            # shellcheck disable=SC2086
            if ! sudo dnf install -y $MISSING_PKGS; then INSTALL_FAIL=true; fi
            
        elif command -v pacman &> /dev/null; then
            # shellcheck disable=SC2086
            if ! sudo pacman -S --noconfirm $MISSING_PKGS; then INSTALL_FAIL=true; fi
            
        else
            echo "[ERROR] Unsupported package manager. Please install $MISSING_PKGS manually."
            exit 1
        fi

        if [ "$INSTALL_FAIL" == true ]; then
            echo "[ERROR] Failed to install system dependencies."
            exit 1
        fi
    else
        echo "[WARNING] Continuing without installing system packages. The app might fail."
    fi
fi

# 3. Virtual Environment (venv) Setup
if [ ! -f "venv/bin/python" ]; then
    echo "[WARNING] The Python virtual environment (venv) was not found."
    read -r -p "Do you want to create the environment and install Python packages now? (y/n): " install_venv
    
    if [[ "$install_venv" =~ ^[Yy]$ ]]; then
        echo "Creating virtual environment..."
        
        if ! python3 -m venv venv; then
            echo "[ERROR] Failed to create venv. Make sure the python venv module is installed."
            exit 1
        fi
        
        echo "Installing dependencies..."
        venv/bin/pip install -r requirements.txt
        
        # Optional: Warns the user about the setcap command to avoid using sudo for Pingator
        echo "---------------------------------------------------"
        echo "[INFO] For Ping3 to work without 'sudo' on Linux, you need to allow Raw Sockets."
        echo "Please run this command manually ONCE to grant permission to the venv:"
        echo "sudo setcap cap_net_raw+ep venv/bin/python"
        echo "---------------------------------------------------"
        
        echo "[SUCCESS] Setup completed!"
    else
        echo "Installation canceled. Exiting..."
        exit 0
    fi
fi

# 4. Streamlit Silent Configuration
# Creates the invisible credentials file with a blank email for Linux
if [ ! -f "$HOME/.streamlit/credentials.toml" ]; then
    mkdir -p "$HOME/.streamlit"
    echo "[general]" > "$HOME/.streamlit/credentials.toml"
    echo "email = \"\"" >> "$HOME/.streamlit/credentials.toml"
fi

# 5. Build Command
if [ "$MODE" == "tray" ]; then
    echo "Starting Pingator in the System Tray..."
    CMD="venv/bin/python tray.py"
else
    echo "Starting Pingator in Web mode..."
    CMD="venv/bin/python -m streamlit run app.py --server.address=0.0.0.0 --browser.gatherUsageStats=false $HEADLESS_FLAG"
fi

# 6. Execution
if [ "$DETACHED" == "true" ]; then
    echo "The process has been sent to the background!"
    
    # Runs Streamlit detached from the terminal securely
    nohup bash -c "$CMD" > /dev/null 2>&1 &
    
    # Fallback message and auto-open browser logic
    if [ "$MODE" == "web" ]; then
        echo "---------------------------------------------------"
        echo "🌐 Pingator is running at: http://localhost:8501"
        echo "(If the browser doesn't open automatically or you are on a headless server, copy and paste this link!)"
        echo "---------------------------------------------------"

        # Forces the default browser to open (Chrome, Brave, Firefox, etc.)
        if [ -z "$HEADLESS_FLAG" ]; then
            sleep 2 # Gives the Python server 2 seconds to start before opening the tab
            
            # gio open works much better on Ubuntu/Wayland and avoids Keyring prompt bugs
            if command -v gio &> /dev/null; then
                gio open "http://localhost:8501" > /dev/null 2>&1
            else
                xdg-open "http://localhost:8501" </dev/null > /dev/null 2>&1
            fi
        fi
    fi
    
    echo "Closing this terminal in 3 seconds..."
    sleep 3
    exit 0
else
    echo "[Debug Mode Activated] Press CTRL+C to stop."
    echo "---------------------------------------------------"
    eval "$CMD"
fi