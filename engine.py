import time
import threading
import subprocess
import platform
import socket
import pandas as pd
from datetime import datetime
from ping3 import ping

from database import init_db

class NetworkEngine:
    def __init__(self, target):
        self.target = target
        self.running = False
        self.ping_thread = None
        self.route_thread = None
        self.route_data = pd.DataFrame() 
        self.raw_traceroute_log = "" 
        self.is_tracing = False      

    def discover_route(self):
        self.is_tracing = True
        hops = []
        is_windows = platform.system().lower() == 'windows'
        
        # Optimize traceroute for speed
        command = ['tracert', '-d', '-h', '15', '-w', '1000', self.target] if is_windows else ['traceroute', '-n', '-m', '15', '-w', '1', self.target]
            
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45)
            
            # Save raw log for the UI Debug panel
            current_time = datetime.now().strftime("%H:%M:%S")
            self.raw_traceroute_log = f"--- Last route update: {current_time} ---\n\n{result.stdout}"
            
            lines = result.stdout.split('\n')
            hop_count = 1
            
            for line in lines:
                if "ms" in line or " * " in line:
                    parts = line.split()
                    ip = "Request timed out"
                    
                    # Extract IP address
                    for part in parts:
                        if part.count('.') == 3 and not part.isalpha():
                            ip = part
                            break
                    
                    # Resolve hostname
                    if ip == "Request timed out":
                        name = "-"
                    else:
                        try:
                            socket.setdefaulttimeout(1)
                            name = socket.gethostbyaddr(ip)[0]
                        except:
                            name = ip
                            
                    # Table headers updated with (ms) and proper order
                    hops.append({
                        "Hop": hop_count, "IP": ip, "Name": name,
                        "Avg (ms)": "-", "Min (ms)": "-", "Max (ms)": "-", "Cur (ms)": "-", "PL%": "-"
                    })
                    hop_count += 1
                    
        except Exception as e:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.raw_traceroute_log = f"--- Error at {current_time} ---\n{str(e)}"
            hops.append({
                "Hop": 1, "IP": "Tracing...", "Name": "Waiting...", 
                "Avg (ms)": "-", "Min (ms)": "-", "Max (ms)": "-", "Cur (ms)": "-", "PL%": "-"
            })
            
        self.route_data = pd.DataFrame(hops)
        self.is_tracing = False

    def start(self):
        self.running = True
        if self.ping_thread is None or not self.ping_thread.is_alive():
            self.ping_thread = threading.Thread(target=self._run_ping, daemon=True)
            self.ping_thread.start()
        if self.route_thread is None or not self.route_thread.is_alive():
            self.route_thread = threading.Thread(target=self._run_route, daemon=True)
            self.route_thread.start()

    def stop(self):
        self.running = False

    def _run_ping(self):
        """Fast loop for latency tracking"""
        conn = init_db()
        c = conn.cursor()

        while self.running:
            ips_to_ping = [self.target]
            if not self.route_data.empty:
                hop_ips = self.route_data['IP'].tolist()
                valid_hops = [ip for ip in hop_ips if ip not in ["Request timed out", "Error parsing route", "Tracing..."]]
                ips_to_ping.extend(valid_hops)
            
            ips_to_ping = list(set(ips_to_ping)) # Remove duplicates
            now = datetime.now()
            
            # Sequential ping to avoid triggering firewall DDoS protections
            for ip in ips_to_ping:
                try:
                    delay = ping(ip, unit='ms', timeout=0.5)
                    if delay is None or delay is False:
                        c.execute("INSERT INTO pings VALUES (?, ?, ?, ?, ?)", (now, self.target, ip, 0, 1))
                    else:
                        c.execute("INSERT INTO pings VALUES (?, ?, ?, ?, ?)", (now, self.target, ip, delay, 0))
                except Exception:
                    c.execute("INSERT INTO pings VALUES (?, ?, ?, ?, ?)", (now, self.target, ip, 0, 1))
            
            conn.commit()
            time.sleep(1)

    def _run_route(self):
        """Slow loop for dynamic route updates"""
        while self.running:
            self.discover_route()
            time.sleep(30) # Wait 30 seconds before re-tracing