# 🚀 Pingator

Pingator is a lightweight, high-performance, multi-target network monitoring and traceroute dashboard. Built with Python and Streamlit, it allows you to track latency, detect packet loss, and map network routes in real-time without locking up your system. And yes, it is entirely vibe-coded.

## ✨ Features

* **Multi-Target Monitoring:** Monitor multiple IP addresses or domains simultaneously.
* **Live Route Discovery:** Automatically maps network hops using native `traceroute` / `tracert`.
* **Background Engine:** Runs completely in the background. The core engine and the UI are decoupled.
* **System Tray Integration:** Minimize the engine to the Windows/Linux system tray to keep it running silently.
* **Interactive Dashboard:** Beautiful, live-updating charts built with Altair and Pandas.
* **Smart Database:** Uses SQLite with WAL optimization and an automatic 2-day data retention cleanup policy.
* **Self-Healing Threads:** Built-in error catching and UI crash notifications to ensure continuous monitoring.
* **One-Click Launchers:** Includes native `.bat` (Windows) and `.sh` (Linux) scripts with automatic virtual environment setup and dependency installation.

## 🛠️ Prerequisites

* **Python 3.8+**
* **Windows:** No additional requirements (uses native `tracert.exe`).
* **Linux:** Requires the `traceroute` utility (`sudo apt install traceroute`).

## 🚀 Installation & Usage

Pingator comes with automated launchers for both Windows and Linux. You do not need to manually create virtual environments or install pip packages.

### For Windows
Run the command prompt **as Administrator** (required for ICMP ping packets):
1. **Standard Web Mode:** Run `pingator.bat` (Starts the background server and opens the UI in your default browser).
2. **System Tray Mode:** Run `pingator.bat --tray` (Starts the engine silently in the system tray).
3. **Debug Mode:** Run `pingator.bat --debug` (Keeps the terminal open to view live logs).

### For Linux
1. Make the script executable: `chmod +x pingator.sh`
2. **Standard Web Mode:** `./pingator.sh`
3. **System Tray Mode:** `./pingator.sh --tray`
4. **Debug Mode:** `./pingator.sh --debug`

## 🛑 Stopping the Engine
Because Pingator runs in the background, closing the terminal or browser will **not** stop the monitoring threads. 
To completely shut down the application, click the red **Quit Engine** button located at the top right of the web interface, or right-click the System Tray icon and select **Exit**.

## 📝 License
This project is open-source and available under the MIT License.