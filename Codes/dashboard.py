import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

data_dir = "Data"
data_file = data_dir + "/baggage_handling.db"

# Set page configuration
st.set_page_config(page_title="Airport Baggage Operations", layout="wide")

# --- Title and Sidebar ---
st.title("✈️ Airport Baggage Operations Dashboard")
st.sidebar.header("Filter Options")
terminal_filter = st.sidebar.multiselect("Select Terminal", ["T1", "T2", "T3"], default=["T1", "T2", "T3"])

# --- Data Loading ---

def load_data():
    conn = sqlite3.connect(data_file)
    # Load events joined with bag metadata
    query = """
    SELECT e.*, b.terminal, b.zone 
    FROM Event e 
    JOIN Bag b ON e.BagID = b.BagID
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

df = load_data()
# Apply filters
df = df[df['terminal'].isin(terminal_filter)]

# --- Top Metric Row ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Bags Processed", df['BagID'].nunique())
col2.metric("Avg Process Delay", f"{round(df['delay'].mean(), 2)} min")
col3.metric("Total Jams", df[df['result'] == 0].shape[0])
col4.metric("Success Rate", f"{round((df['result'].mean() * 100), 1)}%")

st.divider()

# --- Main Dashboard Layout ---
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("Hourly Throughput")
    # Grouping for line chart
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    throughput = df.groupby('hour')['BagID'].nunique().reset_index()
    fig_line = px.line(throughput, x='hour', y='BagID', markers=True, 
                       labels={'BagID': 'Bags', 'hour': 'Hour of Day'},
                       color_discrete_sequence=['#3498db'])
    st.plotly_chart(fig_line, use_container_width=True)

with row1_col2:
    st.subheader("Failure Hotspots (Heatmap)")
    # Pivot for Heatmap
    heatmap_data = df.groupby(['terminal', 'zone'])['result'].apply(lambda x: (x==0).sum()).reset_index()
    fig_heat = px.density_heatmap(heatmap_data, x='zone', y='terminal', z='result', 
                                  color_continuous_scale='Reds', labels={'result': 'Jams'})
    st.plotly_chart(fig_heat, use_container_width=True)

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Sensor Correlation: Temp vs Result")
    fig_box = px.box(df, x='result', y='temp', color='result',
                     labels={'result': 'Success (1) vs Jam (0)', 'temp': 'Temperature (°C)'})
    st.plotly_chart(fig_box, use_container_width=True)

with row2_col2:
    st.subheader("Recent Event Logs")
    st.dataframe(df[['timestamp', 'BagID', 'process', 'delay', 'result']].tail(10), use_container_width=True)