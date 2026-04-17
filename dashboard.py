import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

from database import get_conn

# --- 1. SINGLE LIVE DASHBOARD FRAGMENT (Updates 1s) ---
@st.fragment(run_every=1)
def render_live_dashboard(target_id, engine, minutes_filter, selected_ip_to_graph, chart_h, name_col_w):
    
    # ==========================================
    # --- ERROR DEBUGGER CONSOLE ---------------
    # ==========================================
    engine_error = getattr(engine, 'last_error', None)
    
    # Synchronizes the browser tab title with the error state
    error_exists = engine_error is not None
    if st.session_state.get('title_error_state', False) != error_exists:
        st.session_state.title_error_state = error_exists
        st.rerun() # Forces the whole page to reload to change the title!
        
    if engine_error:
        err_time = getattr(engine, 'error_time', datetime.now()).strftime("%H:%M:%S")
        st.error(f"**Engine Error Detected at {err_time}** - The background thread crashed. Monitoring may be paused.", icon="⚠️")
        with st.expander("Show Stack Trace (For Developers)"):
            st.code(engine_error, language="python")
            if st.button("Clear Log & Dismiss", key=f"clear_err_{target_id}"):
                engine.last_error = None
                engine.error_time = None
                st.session_state.title_error_state = False
                st.rerun()
    # ==========================================

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
        last_pings_df = pd.read_sql_query(
            "SELECT pinged_ip, latency, packet_loss FROM pings WHERE main_target = ? ORDER BY timestamp DESC LIMIT 50", 
            conn, params=(target_id,)
        )
        
        stats_df = pd.read_sql_query(
            '''SELECT pinged_ip, 
                      COUNT(*) as total, 
                      SUM(packet_loss) as loss,
                      AVG(CASE WHEN packet_loss = 0 THEN latency END) as avg_lat,
                      MIN(CASE WHEN packet_loss = 0 THEN latency END) as min_lat,
                      MAX(CASE WHEN packet_loss = 0 THEN latency END) as max_lat
               FROM pings 
               WHERE main_target = ? AND timestamp >= ? 
               GROUP BY pinged_ip''', 
            conn, params=(target_id, time_limit)
        )
        
        stats_dict = stats_df.set_index('pinged_ip').to_dict('index')
        
        cur_pings = {}
        for _, row in last_pings_df.iterrows():
            ip = row['pinged_ip']
            if ip not in cur_pings:
                cur_pings[ip] = row['latency'] if row['packet_loss'] == 0 else "Timeout"

        for index, row in display_df.iterrows():
            ip = row['IP']
            if ip not in ["Request timed out", "Error parsing route", "Tracing..."]:
                if ip in stats_dict:
                    s = stats_dict[ip]
                    total = s['total']
                    loss = s['loss']
                    display_df.at[index, 'PL%'] = f"{(loss/total)*100:.1f}%" if total > 0 else "0.0%"
                    
                    if pd.notna(s['avg_lat']):
                        display_df.at[index, 'Avg (ms)'] = f"{s['avg_lat']:.1f}"
                        display_df.at[index, 'Min (ms)'] = f"{s['min_lat']:.1f}"
                        display_df.at[index, 'Max (ms)'] = f"{s['max_lat']:.1f}"

                if ip in cur_pings:
                    val = cur_pings[ip]
                    display_df.at[index, 'Cur (ms)'] = f"{val:.1f}" if isinstance(val, (int, float)) else val

        correct_columns = ["Hop", "IP", "Name", "Avg (ms)", "Min (ms)", "Max (ms)", "Cur (ms)", "PL%"]
        if all(col in display_df.columns for col in correct_columns):
            display_df = display_df[correct_columns]

        # --- Fixed Column Widths Configuration ---
        st.dataframe(
            display_df, 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "Hop": st.column_config.NumberColumn("Hop", width="small"),
                "IP": st.column_config.TextColumn("IP", width="medium"),
                "Name": st.column_config.TextColumn("Name", width=name_col_w),
                "Avg (ms)": st.column_config.TextColumn("Avg (ms)", width="small"),
                "Min (ms)": st.column_config.TextColumn("Min (ms)", width="small"),
                "Max (ms)": st.column_config.TextColumn("Max (ms)", width="small"),
                "Cur (ms)": st.column_config.TextColumn("Cur (ms)", width="small"),
                "PL%": st.column_config.TextColumn("PL%", width="small")
            }
        )
    elif not getattr(engine, 'is_tracing', False) and engine.running:
        st.info("Waiting for the first routing cycle...")

    st.markdown("#### Latency Chart")

    df = pd.read_sql_query(
        "SELECT timestamp, latency, packet_loss FROM pings WHERE main_target = ? AND pinged_ip = ? AND timestamp >= ?", 
        conn, params=(target_id, selected_ip_to_graph, time_limit), parse_dates=['timestamp']
    )

    if not df.empty:
        max_y = df['latency'].max() if df['latency'].max() > 0 else 100
        
        if len(df) > 400:
            freq_seconds = max(1, (minutes_filter * 60) // 400)
            freq_str = f"{freq_seconds}s" 
            
            df_idx = df.set_index('timestamp')
            
            df_success = df_idx[df_idx['packet_loss'] == 0]
            df_success_chart = df_success.resample(freq_str)['latency'].mean().reset_index().dropna()
            
            df_loss = df_idx[df_idx['packet_loss'] == 1]
            if not df_loss.empty:
                df_loss_chart = df_loss.resample(freq_str)['packet_loss'].max().reset_index().dropna()
                df_loss_chart = df_loss_chart[df_loss_chart['packet_loss'] == 1.0]
            else:
                df_loss_chart = pd.DataFrame(columns=['timestamp', 'packet_loss'])
        else:
            df_success_chart = df[df['packet_loss'] == 0]
            df_loss_chart = df[df['packet_loss'] == 1].copy()
        
        area_chart = alt.Chart(df_success_chart).mark_area(
            opacity=0.3,
            color='#0068c9',
            line={'color': '#0068c9', 'strokeWidth': 2}
        ).encode(
            x=alt.X('timestamp:T', title='Time', axis=alt.Axis(format='%H:%M:%S', gridColor='rgba(255,255,255,0.05)')),
            y=alt.Y('latency:Q', title='Milliseconds (ms)', axis=alt.Axis(gridColor='rgba(255,255,255,0.05)')),
            tooltip=['timestamp:T', 'latency:Q']
        )

        if not df_loss_chart.empty:
            df_loss_chart['loss_height'] = max_y * 1.1 
            loss_bars = alt.Chart(df_loss_chart).mark_bar(
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
        c2.metric("Avg Latency", f"{df[df['packet_loss'] == 0]['latency'].mean():.1f} ms")
        c3.metric("Peak Latency", f"{df['latency'].max():.1f} ms")
        c4.metric("Packets Lost", f"{df['packet_loss'].sum()} ({ (df['packet_loss'].sum() / len(df)) * 100:.1f}%)")
    else:
        st.info(f"Waiting for data for {selected_ip_to_graph}...")

    st.write("")
@st.fragment(run_every=15)
def render_debug_log(engine):
    with st.expander(":material/bug_report: Expandable Traceroute Debug"):
        log = getattr(engine, 'raw_traceroute_log', '')
        if log:
            st.code(log, language="text")
        else:
            st.write("No traceroute executed yet. Wait for the loading cycle.")