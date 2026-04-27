import time
import threading
import subprocess
import platform
import socket
import pandas as pd
import traceback 
from datetime import datetime
from ping3 import ping

from database import init_db, cleanup_old_pings, get_conn 

class NetworkEngine:
    def __init__(self, target):
        self.target = target
        self.running = False
        self.ping_thread = None
        self.route_thread = None
        self.route_data = pd.DataFrame() 
        self.raw_traceroute_log = "" 
        self.is_tracing = False 
        self.is_active_ui = False # <--- NOVO: Sabe se está na tela ou no background
        
        # --- Error tracking variables ---
        self.last_error = None
        self.error_time = None     

    def discover_route(self):
        self.is_tracing = True
        hops = []
        is_windows = platform.system().lower() == 'windows'
        
        # Optimize traceroute for speed
        command = ['tracert', '-d', '-h', '15', '-w', '1000', self.target] if is_windows else ['traceroute', '-n', '-m', '15', '-w', '1', self.target]
            
        try:
            if is_windows:
                # 0x08000000 is CREATE_NO_WINDOW. It forces the tracert process to be completely invisible!
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45, creationflags=0x08000000)
            else:
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
                            
                    # Table headers with (ms) and proper order
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
        # Clear previous errors when starting
        self.last_error = None 
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
        while self.running:
            try:
                ips_to_ping = [self.target]
                if not self.route_data.empty:
                    hop_ips = self.route_data['IP'].tolist()
                    valid_hops = [ip for ip in hop_ips if ip not in ["Request timed out", "Error parsing route", "Tracing..."]]
                    ips_to_ping.extend(valid_hops)
                
                ips_to_ping = list(set(ips_to_ping)) # Remove duplicates
                now = datetime.now()
                
                # 1. RUN PINGS FIRST
                ping_results = []
                for ip in ips_to_ping:
                    try:
                        delay = ping(ip, unit='ms', timeout=0.5)
                        if delay is None or delay is False:
                            ping_results.append((now, self.target, ip, 0, 1))
                        else:
                            ping_results.append((now, self.target, ip, delay, 0))
                    except Exception:
                        ping_results.append((now, self.target, ip, 0, 1))
                    
                    # Anti-flood protection (100ms)
                    time.sleep(0.1)
                
                # 2. SAVE TO DATABASE
                try:
                    conn = get_conn()
                    c = conn.cursor()
                    c.executemany("INSERT INTO pings VALUES (?, ?, ?, ?, ?)", ping_results)
                    conn.commit()
                except Exception as e:
                    raise e
                finally:
                    if 'conn' in locals():
                        conn.close()
                
                # --- 3. SMART SLEEP (Active vs Background) ---
                # 1s for the active UI tab, 2s for background tabs
                target_sleep = 1 if self.is_active_ui else 2
                slept = 0
                
                while slept < target_sleep and self.running:
                    time.sleep(1)
                    slept += 1
                    
                    # Wake up instantly if the user clicks on this background tab!
                    if self.is_active_ui and target_sleep == 2:
                        break
                
            except Exception as e:
                self.last_error = traceback.format_exc()
                self.error_time = datetime.now()
                time.sleep(2) 

    def _run_route(self):
        """Slow loop for dynamic route updates and DB maintenance"""
        loop_counter = 0
        while self.running:
            try:
                # --- UPDATE ROUTE LESS FREQUENTLY IF IN BACKGROUND ---
                # Route trace takes time. Skip some traces if we are in background.
                self.discover_route()
                
                # Runs the database cleanup approximately every 1 hour (120 loops of 30s)
                loop_counter += 1
                if loop_counter >= 120:
                    try:
                        cleanup_old_pings()
                    except Exception as e:
                        raise e 
                    loop_counter = 0
                    
            except Exception as e:
                self.last_error = traceback.format_exc()
                self.error_time = datetime.now()
                
            time.sleep(30)