#!/bin/bash

# Colors for terminal formatting
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=======================================${NC}"
echo -e "${CYAN}    🚀 Pingator Launcher (Linux)      ${NC}"
echo -e "${CYAN}=======================================${NC}"

# --- PARAMETER READING ---
MODE="web"
DETACHED=true

for arg in "$@"; do
    if [ "$arg" == "--tray" ]; then
        MODE="tray"
    elif [ "$arg" == "--debug" ]; then
        DETACHED=false
    fi
done

# 1. Check and install system traceroute
if ! command -v traceroute &> /dev/null; then
    echo -e "${YELLOW}The system utility 'traceroute' was not found.${NC}"
    read -p "Do you want to install traceroute now? (y/n): " install_tr
    
    if [[ "$install_tr" == "y" || "$install_tr" == "Y" ]]; then
        echo -e "\n${GREEN}Detecting package manager and installing...${NC}"
        
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y traceroute
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y traceroute
        elif command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm traceroute
        else
            echo -e "${YELLOW}Could not detect the package manager. Please install traceroute manually.${NC}"
        fi
        echo -e "${GREEN}Traceroute verification completed!${NC}\n"
    else
        echo -e "${YELLOW}Warning: The route mapping function (traceroute) will not work without this package.${NC}\n"
    fi
fi

# 2. Interactive Virtual Environment (venv) Setup
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}The Python virtual environment (venv) and dependencies were not found.${NC}"
    read -p "Do you want to create the environment and install Python packages now? (y/n): " install_venv
    
    if [[ "$install_venv" == "y" || "$install_venv" == "Y" ]]; then
        echo -e "\n${GREEN}Creating virtual environment...${NC}"
        python3 -m venv venv
        
        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}Error creating venv. Trying to automatically install the python3-venv package...${NC}"
            if command -v apt &> /dev/null; then
                sudo apt update && sudo apt install -y python3-venv
                python3 -m venv venv
            else
                echo -e "${YELLOW}Please install the python3-venv package manually and try again.${NC}"
                exit 1
            fi
        fi

        echo "Installing dependencies (this may take a minute)..."
        ./venv/bin/pip install -r requirements.txt
        
        echo -e "${GREEN}Python setup completed successfully!${NC}\n"
    else
        echo -e "${YELLOW}Installation canceled. Exiting...${NC}"
        exit 0
    fi
fi

# 3. Request Sudo Password Upfront
echo -e "${YELLOW}Requesting administrator privileges (sudo) for network monitoring...${NC}"
sudo -v # Prompts and validates the user's password here to avoid hanging in the background

# 4. Base Command Configuration
if [ "$MODE" == "tray" ]; then
    echo -e "${GREEN}Starting Pingator in the System Tray...${NC}"
    CMD="sudo ./venv/bin/python tray.py"
else
    echo -e "${GREEN}Starting Pingator in Web mode...${NC}"
    CMD="sudo ./venv/bin/streamlit run app.py --server.address=0.0.0.0"
fi

# 5. Execution (Background vs Debug)
if [ "$DETACHED" = true ]; then
    echo -e "${YELLOW}The process has been sent to the background! You can now close this terminal.${NC}"
    nohup $CMD > /dev/null 2>&1 &
    disown
    exit 0
else
    echo -e "${CYAN}Debug mode activated. Keeping the terminal open to display logs.${NC}"
    echo -e "${CYAN}Press CTRL+C to stop Pingator.${NC}"
    echo "---------------------------------------------------"
    $CMD
fi