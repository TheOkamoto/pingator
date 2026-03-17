import pystray
from PIL import Image, ImageDraw
import subprocess
import sys
import os

# Global reference to the background Streamlit process
streamlit_process = None

def create_icon():
    """Draws a simple bar chart icon for the System Tray"""
    image = Image.new('RGB', (64, 64), color=(30, 30, 30))
    draw = ImageDraw.Draw(image)
    draw.rectangle([10, 40, 20, 60], fill=(0, 104, 201))
    draw.rectangle([25, 25, 35, 60], fill=(0, 104, 201))
    draw.rectangle([40, 10, 50, 60], fill=(255, 0, 0))
    return image

def start_background_engine():
    """Starts the Streamlit server completely hidden"""
    global streamlit_process
    if streamlit_process is None:
        flags = 0x08000000 if os.name == 'nt' else 0 
        
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags
        )

def open_interface(icon, item):
    """Opens the Electron-style interface via Edge/Chrome"""
    flags = 0x08000000 if os.name == 'nt' else 0
    subprocess.Popen(
        ["start", "msedge", "--app=http://localhost:8501"], 
        shell=True,
        creationflags=flags
    )

def exit_app(icon, item):
    """Kills the network monitoring process and exits"""
    global streamlit_process
    if streamlit_process:
        streamlit_process.terminate()
    icon.stop()

def setup_tray():
    start_background_engine()
    
    menu = pystray.Menu(
        pystray.MenuItem('Open Interface', open_interface, default=True),
        pystray.MenuItem('Exit (Stop Monitoring)', exit_app)
    )
    
    image = create_icon()
    icon = pystray.Icon("Pingator", image, "Pingator - Network Monitor", menu)
    
    icon.run()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    setup_tray()