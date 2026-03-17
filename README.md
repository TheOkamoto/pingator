# 📈 Pingator - Multi-Target & Route Monitor

**Pingator** is a lightweight, modern, and persistent network monitoring tool built with Python and Streamlit. It allows you to track ICMP latency, packet loss, and dynamic routing (traceroute) across multiple targets simultaneously, all visualized in a sleek, real-time dashboard.

## ✨ Key Features

* **Multi-Target Monitoring**: Ping multiple domains or IP addresses concurrently using background threads.
* **Dynamic Traceroute**: Automatically discovers and monitors all hops in the route to your target.
* **Real-Time Analytics**: Visualizes latency and packet loss using interactive, auto-updating Altair area charts.
* **HDD-Friendly Database**: Uses an optimized SQLite database (WAL mode, memory caching) to ensure high performance without stressing mechanical hard drives.
* **Persistent UI States**: Remembers your targets, custom timeframes, and UI layout preferences (chart heights) across sessions.
* **System Tray Integration**: Run it silently in the background with a system tray icon for easy access.
* **Local Network Access**: Access your dashboard from your phone or another PC on the same Wi-Fi network.

---

## 🚀 Prerequisites

* **Python 3.8+** installed on your system.
* **Administrator / Root Privileges**: Required because the `ping3` library needs elevated permissions to send raw ICMP packets.

---

## 🛠️ Installation

1. **Clone the repository:**

   $ git clone https://github.com/TheOkamoto/pingator.git
   $ cd pingator


2. **Create a virtual environment (Recommended):**

   $ python -m venv venv
   
   *On Windows:*
   $ venv\Scripts\activate
   
   *On macOS/Linux:*
   $ source venv/bin/activate


3. **Install the dependencies:**

   $ pip install -r requirements.txt

---

## 🎮 Usage

There are two ways to run Pingator, depending on your needs.

> ⚠️ **Important:** Always open your terminal as an Administrator (Windows) or use `sudo` (Linux/Mac) before running the app.

### Option A: System Tray / Background Mode (Recommended)
If you want the engine to run silently in the background without keeping a terminal window open, run the tray script. An icon will appear in your system tray where you can open the UI.

   $ python tray.py


### Option B: Standard Web App Mode
This runs the application directly in your terminal and opens the UI in your default web browser.

   $ streamlit run app.py

---

## 📱 Accessing from your Phone (Local Network)

You can view your Pingator dashboard from any device on the same Wi-Fi network!

1. **Start the app explicitly exposing the network address:**

   $ streamlit run app.py --server.address=0.0.0.0


2. **Find your PC's local IP address** (e.g., 192.168.1.2).

3. **Open a browser on your phone and go to:** http://192.168.1.2:8501


> 💡 **Note for Windows Users:** If the page doesn't load on your phone, your Windows Firewall might be blocking port 8501. You can allow it by running this command in PowerShell (Admin):

   PS> New-NetFirewallRule -DisplayName "Pingator Port 8501" -Direction Inbound -LocalPort 8501 -Protocol TCP -Action Allow