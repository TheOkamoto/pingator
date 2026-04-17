import streamlit as st
import time
import os

# --- IMPORT OUR NEW MODULES ---
from utils import get_base64_image, load_local_css
from dashboard import render_live_dashboard, render_debug_log

from database import (
    init_db, get_saved_targets, add_saved_target, 
    remove_saved_target, update_timeframe, get_timeframe,
    get_last_tab, set_last_tab, get_setting, set_setting
)
from engine import NetworkEngine

# Setup Icons and CSS
icon_b64 = get_base64_image("icon.png")
if icon_b64:
    icon_html = f"<img src='data:image/png;base64,{icon_b64}' width='32' height='32' style='border-radius: 6px; object-fit: contain;'>"
    page_icon_config = "icon.png"
else:
    icon_html = "🌐"
    page_icon_config = "🌐"

@st.cache_resource
def get_engines():
    return {} 

engines = get_engines()
init_db() 

# --- DYNAMIC TAB TITLE MAGIC ---
if "title_error_state" not in st.session_state:
    st.session_state.title_error_state = False

if "target_selector" in st.session_state:
    active_tab = st.session_state.target_selector
else:
    active_tab = get_last_tab()

error_prefix = "(1) Notification - " if st.session_state.title_error_state else ""
dynamic_page_title = f"{error_prefix}Pingator - {active_tab}" if active_tab else f"{error_prefix}Pingator"

st.set_page_config(page_title=dynamic_page_title, page_icon=page_icon_config, layout="wide", initial_sidebar_state="collapsed")
load_local_css("style.css")

if "targets" not in st.session_state:
    st.session_state.targets = get_saved_targets()
    for t in st.session_state.targets:
        if t not in engines:
            engines[t] = NetworkEngine(t)
            engines[t].start()

# --- ALIGNED TITLE & CONTROL BUTTONS ---
col_title, col_input, col_add, col_restart, col_quit = st.columns([2.5, 3.5, 2, 2, 2])

with col_title:
    st.markdown(f"""
        <div style='height: 40px; display: flex; align-items: center;'>
            <h3 style='margin: 0; display: flex; align-items: center; gap: 8px;'>
                {icon_html}
                Pingator
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
with col_input:
    new_target = st.text_input("Add new target", placeholder="e.g., discord.com", label_visibility="collapsed")
    
with col_add:
    if st.button(":material/add: Add Target", width="stretch") and new_target:
        if new_target not in st.session_state.targets:
            add_saved_target(new_target) 
            st.session_state.targets.append(new_target) 
            engines[new_target] = NetworkEngine(new_target)
            engines[new_target].start() 
            set_last_tab(new_target) 
            st.rerun()

with col_restart:
    if st.button(":material/restart_alt: Restart", width="stretch", help="Restarts all background engines"):
        for eng in engines.values():
            eng.stop()
        get_engines.clear()
        st.toast("Restarting engines...")
        time.sleep(0.5)
        st.rerun()

with col_quit:
    if st.button(":material/power_settings_new: Quit", type="primary", width="stretch", help="Shuts down the application completely"):
        for eng in engines.values():
            eng.stop()
        st.toast("Shutting down server... You can close this browser tab.")
        time.sleep(1) 
        os._exit(0)

st.write("") 

if not st.session_state.targets:
    st.info("No targets configured. Add a domain or IP above to start.")
    st.stop()

# --- TARGET NAVIGATION ---
last_tab = get_last_tab()
try:
    default_index = st.session_state.targets.index(last_tab)
except ValueError:
    default_index = 0

selected_target = st.radio(
    "Monitoring Targets:", 
    st.session_state.targets, 
    index=default_index,
    horizontal=True,
    label_visibility="collapsed",
    key="target_selector" 
)

if selected_target != last_tab:
    set_last_tab(selected_target)

target_id = selected_target

if target_id not in engines:
    engines[target_id] = NetworkEngine(target_id)
    
engine = engines[target_id]

# --- TAB CONTROLS ---
c_btn1, c_btn2, c_btn3, c_status = st.columns([1, 1, 1, 3])
with c_btn1:
    if st.button(f":material/play_arrow: Start", key=f"start_{target_id}", width="stretch"):
        engine.start()
        st.rerun()
with c_btn2:
    if st.button(f":material/stop: Stop", key=f"stop_{target_id}", width="stretch"):
        engine.stop()
        st.rerun()
with c_btn3:
    if st.button(f":material/delete: Remove", key=f"del_{target_id}", width="stretch"):
        engine.stop() 
        remove_saved_target(target_id) 
        st.session_state.targets.remove(target_id)
        if target_id in engines:
            del engines[target_id] 
        st.rerun()
        
with c_status:
    if engine.running:
        st.markdown(f'<div style="height: 38px; display: flex; align-items: center; justify-content: center; border-radius: 0.5rem; background-color: rgba(43, 158, 64, 0.1); border: 1px solid rgba(43, 158, 64, 0.4); color: #8ce196; font-size: 0.9rem;"><span style="height: 10px; width: 10px; background-color: #57d06c; border-radius: 50%; display: inline-block; margin-right: 8px; box-shadow: 0 0 8px #57d06c;"></span> Monitoring&nbsp;<b>{target_id}</b>&nbsp;and route hops.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="height: 38px; display: flex; align-items: center; justify-content: center; border-radius: 0.5rem; background-color: rgba(255, 75, 75, 0.1); border: 1px solid rgba(255, 75, 75, 0.4); color: #ff8c8c; font-size: 0.9rem;"><span style="height: 10px; width: 10px; background-color: #ff6b6b; border-radius: 50%; display: inline-block; margin-right: 8px; box-shadow: 0 0 8px #ff6b6b;"></span> Stopped.</div>', unsafe_allow_html=True)

st.write("") 

# --- INPUT WIDGETS ---
time_options = {
    '1 Minute': 1, '10 Min': 10, '30 Min': 30, 
    '1 Hour': 60, '3 Hours': 180, '24 Hours': 1440
}

saved_tf = get_timeframe(target_id)
keys_list = list(time_options.keys())
values_list = list(time_options.values())

try:
    default_index_tf = values_list.index(saved_tf)
except ValueError:
    default_index_tf = 1 

c_time, c_ip, c_layout = st.columns([3, 4, 2])

with c_time:
    selected_label = st.selectbox("Timeframe:", keys_list, index=default_index_tf, key=f"time_{target_id}")
    minutes_filter = time_options[selected_label]
    if minutes_filter != saved_tf:
        update_timeframe(target_id, minutes_filter)

with c_ip:
    available_ips = [target_id]
    if not engine.route_data.empty:
        valid_hops = [ip for ip in engine.route_data['IP'].tolist() if ip not in ["Request timed out", "Error parsing route", "Tracing..."]]
        available_ips.extend(valid_hops)
        
    selected_ip_to_graph = st.selectbox(
        "Select IP/Hop to view chart:", 
        list(dict.fromkeys(available_ips)),
        key=f"chart_ip_select_{target_id}"
    )

with c_layout:
    st.markdown("<div style='font-size: 0.85rem; color: rgba(250, 250, 250, 0.6); margin-bottom: 0.25rem;'>UI Settings:</div>", unsafe_allow_html=True)
    with st.popover(":material/settings: Layout Options", width="stretch"):
        
        # Chart Height setting
        chart_h = st.slider("Chart Height (px)", 150, 800, get_setting('chart_height', 250), step=10)
        if chart_h != get_setting('chart_height', 250):
            set_setting('chart_height', chart_h)
            
        # Name Column Width setting
        name_col_w = st.slider("Name Col Width (px)", 100, 800, get_setting('name_col_width', 300), step=10)
        if name_col_w != get_setting('name_col_width', 300):
            set_setting('name_col_width', name_col_w)

# --- CALL THE IMPORTED FRAGMENTS ---
# 1. The ultra-fast fragment for the chart (Updates 1s)
render_live_dashboard(target_id, engine, minutes_filter, selected_ip_to_graph, chart_h, name_col_w)

# 2. The slow fragment for the logs (Updates 15s)
render_debug_log(engine)