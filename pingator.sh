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

# 2. Virtual Environment (venv) Setup
if [ ! -f "venv/bin/python" ]; then
    echo "[WARNING] The Python virtual environment (venv) was not found."
    read -p "Do you want to create the environment and install packages now? (y/n): " install_venv
    
    if [[ "$install_venv" =~ ^[Yy]$ ]]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            echo "[ERROR] Failed to create venv. Make sure python3-venv is installed."
            exit 1
        fi
        echo "Installing dependencies..."
        venv/bin/pip install -r requirements.txt
        echo "[SUCCESS] Setup completed!"
    else
        echo "Installation canceled. Exiting..."
        exit 0
    fi
fi

# 3. Streamlit Silent Configuration (The Magic for New Users)
# Creates the invisible credentials file with a blank email for Linux
if [ ! -f "$HOME/.streamlit/credentials.toml" ]; then
    mkdir -p "$HOME/.streamlit"
    echo "[general]" > "$HOME/.streamlit/credentials.toml"
    echo "email = \"\"" >> "$HOME/.streamlit/credentials.toml"
fi

# 4. Build Command
if [ "$MODE" == "tray" ]; then
    echo "Starting Pingator in the System Tray..."
    CMD="venv/bin/python tray.py"
else
    echo "Starting Pingator in Web mode..."
    CMD="venv/bin/python -m streamlit run app.py --server.address=0.0.0.0 --browser.gatherUsageStats=false $HEADLESS_FLAG"
fi

# 5. Execution
if [ "$DETACHED" == "true" ]; then
    echo "The process has been sent to the background!"
    
    # Runs Streamlit detached from the terminal
    nohup $CMD > /dev/null 2>&1 &
    
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
    eval $CMD
fi