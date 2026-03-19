import streamlit as st
import pandas as pd
import altair as alt
import base64
import os
from datetime import datetime, timedelta

from database import (
    get_conn, init_db, get_saved_targets, add_saved_target, 
    remove_saved_target, update_timeframe, get_timeframe,
    get_last_tab, set_last_tab, get_setting, set_setting
)
from engine import NetworkEngine

# --- ASSET LOADING FUNCTIONS ---
def get_base64_image(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

def load_local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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
# Read from session or database BEFORE setting page config
if "target_selector" in st.session_state:
    active_tab = st.session_state.target_selector
else:
    active_tab = get_last_tab()

if active_tab:
    dynamic_page_title = f"Pingator - Multi-Target & Route Monitor - {active_tab}"
else:
    dynamic_page_title = "Pingator - Multi-Target & Route Monitor"

# Apply the dynamic title to the browser tab!
st.set_page_config(page_title=dynamic_page_title, page_icon=page_icon_config, layout="wide", initial_sidebar_state="collapsed")

# LOAD OUR EXTERNAL CSS FILE HERE! 🪄
load_local_css("style.css")

if "targets" not in st.session_state:
    st.session_state.targets = get_saved_targets()
    for t in st.session_state.targets:
        if t not in engines:
            engines[t] = NetworkEngine(t)
            engines[t].start()

# --- ALIGNED TITLE ---
col_title, col_input, col_btn = st.columns([2, 7, 2])
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
    new_target = st.text_input("Add new target", placeholder="Put a website URL here", label_visibility="collapsed")
with col_btn:
    if st.button(":material/add: Add Target", width="stretch") and new_target:
        if new_target not in st.session_state.targets:
            add_saved_target(new_target) 
            st.session_state.targets.append(new_target) 
            engines[new_target] = NetworkEngine(new_target)
            engines[new_target].start() 
            set_last_tab(new_target) 
            st.rerun()

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
    key="target_selector"  # <-- The key that allows the title to read this selection at the top!
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
    st.markdown("<div style='font-size: 0.85rem; color: rgba(250, 250, 250, 0.6); margin-bottom: 0.25rem;'>Chart Size:</div>", unsafe_allow_html=True)
    with st.popover(":material/settings: Resize Chart", width="stretch"):
        chart_h = st.slider("Height (px)", 150, 800, get_setting('chart_height', 250), step=10)
        if chart_h != get_setting('chart_height', 250):
            set_setting('chart_height', chart_h)

# --- SINGLE LIVE DASHBOARD FRAGMENT ---
@st.fragment(run_every=1)
def render_live_dashboard(target_id, engine, minutes_filter, selected_ip_to_graph, chart_h):
    conn = get_conn() 
    time_limit = datetime.now() - timedelta(minutes=minutes_filter)

    col_title, col_spin = st.columns([2, 8])
    with col_title:
        st.markdown("#### Route Information")
    
    if getattr(engine, 'is_tracing', False):
        with col_spin:
            with st.spinner("Discovering..."):
                st.empty()
    
    display_df = engine.route_data.copy()
    if not display_df.empty:
        df_stats = pd.read_sql_query(
            "SELECT pinged_ip, latency, packet_loss FROM pings WHERE main_target = ? AND timestamp >= ?", 
            conn, params=(target_id, time_limit)
        )
        
        if not df_stats.empty:
            for index, row in display_df.iterrows():
                ip = row['IP']
                if ip not in ["Request timed out", "Error parsing route", "Tracing..."]:
                    ip_data = df_stats[df_stats['pinged_ip'] == ip]
                    if not ip_data.empty:
                        total = len(ip_data)
                        loss = ip_data['packet_loss'].sum()
                        success_data = ip_data[ip_data['packet_loss'] == 0]
                        
                        display_df.at[index, 'PL%'] = f"{(loss/total)*100:.1f}%"
                        if not success_data.empty:
                            display_df.at[index, 'Avg (ms)'] = f"{success_data['latency'].mean():.1f}"
                            display_df.at[index, 'Min (ms)'] = f"{success_data['latency'].min():.1f}"
                            display_df.at[index, 'Max (ms)'] = f"{success_data['latency'].max():.1f}"
                            display_df.at[index, 'Cur (ms)'] = f"{success_data.iloc[-1]['latency']:.1f}"

        correct_columns = ["Hop", "IP", "Name", "Avg (ms)", "Min (ms)", "Max (ms)", "Cur (ms)", "PL%"]
        if all(col in display_df.columns for col in correct_columns):
            display_df = display_df[correct_columns]

        st.dataframe(display_df, hide_index=True, width="stretch")
    elif not getattr(engine, 'is_tracing', False) and engine.running:
        st.info("Waiting for the first routing cycle...")

    st.markdown("#### Latency Chart")

    df = pd.read_sql_query(
        "SELECT * FROM pings WHERE main_target = ? AND pinged_ip = ? AND timestamp >= ?", 
        conn, params=(target_id, selected_ip_to_graph, time_limit), parse_dates=['timestamp']
    )

    if not df.empty:
        max_y = df['latency'].max() if df['latency'].max() > 0 else 100
        
        df_success = df[df['packet_loss'] == 0]
        area_chart = alt.Chart(df_success).mark_area(
            opacity=0.3,
            color='#0068c9',
            line={'color': '#0068c9', 'strokeWidth': 2}
        ).encode(
            x=alt.X('timestamp:T', title='Time', axis=alt.Axis(format='%H:%M:%S', gridColor='rgba(255,255,255,0.05)')),
            y=alt.Y('latency:Q', title='Milliseconds (ms)', axis=alt.Axis(gridColor='rgba(255,255,255,0.05)')),
            tooltip=['timestamp:T', 'latency:Q']
        )

        df_loss = df[df['packet_loss'] == 1].copy()
        if not df_loss.empty:
            df_loss['loss_height'] = max_y * 1.1 
            loss_bars = alt.Chart(df_loss).mark_bar(
                color='red', 
                size=3 
            ).encode(
                x='timestamp:T',
                y=alt.Y('loss_height:Q'),
                tooltip=['timestamp:T']
            )
            final_chart = alt.layer(area_chart, loss_bars)
        else:
            final_chart = area_chart

        final_chart = final_chart.properties(
            height=chart_h
        ).configure_view(
            strokeWidth=0
        )

        st.altair_chart(final_chart, width="stretch")
        
        last_ping = df.iloc[-1]
        if last_ping['packet_loss'] == 1:
            cur_lat_str = "Timeout"
        else:
            cur_lat_str = f"{last_ping['latency']:.1f} ms"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"Cur Latency ({selected_ip_to_graph})", cur_lat_str)
        c2.metric("Avg Latency", f"{df['latency'].mean():.1f} ms")
        c3.metric("Peak Latency", f"{df['latency'].max():.1f} ms")
        c4.metric("Packets Lost", f"{df['packet_loss'].sum()} ({ (df['packet_loss'].sum() / len(df)) * 100:.1f}%)")
    else:
        st.info(f"Waiting for data for {selected_ip_to_graph}...")

    st.write("")
    
    with st.expander(":material/bug_report: Expandable Traceroute Debug"):
        log = getattr(engine, 'raw_traceroute_log', '')
        if log:
            st.code(log, language="text")
        else:
            st.write("No traceroute executed yet. Wait for the loading cycle.")

render_live_dashboard(target_id, engine, minutes_filter, selected_ip_to_graph, chart_h)