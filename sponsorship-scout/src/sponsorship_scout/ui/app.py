import streamlit as st
import sqlite3
import pandas as pd
import streamlit as st
import sqlite3
import pandas as pd
import os
import yaml
import asyncio
from sponsorship_scout.core.config import load_config
from sponsorship_scout.core.engine import run_engine

st.set_page_config(page_title="Sponsorship Scout", layout="wide", page_icon="🇬🇧")

st.markdown("""
<style>
/* Professional Startup Style */
.stButton>button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}
h1, h2, h3 {
    color: #1E3A8A;
}
div[data-testid="stMetricValue"] {
    color: #2563EB;
}
</style>
""", unsafe_allow_html=True)

st.title("🇬🇧 Sponsorship Scout Dashboard")
st.markdown("Welcome to your local UK visa sponsorship job tracker. This dashboard visualizes jobs scraped from your configured SQLite destinations.")

config_path = os.environ.get('SPONSOR_SCOUT_CONFIG', 'config.yaml')
cfg = load_config(config_path)
sqlite_tables = []
for profile in cfg.profiles:
    for dest in profile.destinations:
        if dest.type == 'sqlite':
            sqlite_tables.append((profile.name, dest.table_name))

if not sqlite_tables:
    st.warning("No SQLite destinations configured in your profiles. Add one to view jobs here!")
    st.stop()

# Add a sidebar button to run the scraper directly from the UI
with st.sidebar:
    st.header("⚙️ Actions")
    st.markdown("Manually trigger a scan of all profiles in your configuration.")
    if st.button("🔄 Run Scraper Now", use_container_width=True):
        with st.spinner("Scraping ATS platforms... This may take a couple of minutes."):
            cfg = load_config(config_path)
            asyncio.run(run_engine(cfg))
        st.success("Scraping complete! Refreshing data...")
        st.rerun()
    
    st.divider()
    st.subheader("Filter Data")
    profile_name, table_name = st.selectbox("Select Profile", sqlite_tables, format_func=lambda x: x[0])

try:
    conn = sqlite3.connect('sponsorship_scout.db')
    df = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY added_date DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("No jobs found in the database yet. Click 'Run Scraper Now' in the sidebar to get started!")
    else:
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Jobs Found", len(df))
        with col2:
            st.metric("Companies", df['company'].nunique())
        with col3:
            latest_date = df['added_date'].max()
            st.metric("Latest Scan", latest_date)
            
        st.divider()
        st.subheader(f"Latest Jobs for Profile: `{profile_name}`")
        st.dataframe(
            df[['added_date', 'company', 'title', 'location', 'url']], 
            use_container_width=True,
            column_config={
                "url": st.column_config.LinkColumn("Apply Link"),
                "added_date": "Date Added",
                "company": "Company",
                "title": "Job Title",
                "location": "Location"
            },
            hide_index=True
        )
except Exception:
    st.info("👋 **Welcome to Sponsorship Scout!**\n\nYour database is currently empty because you haven't run a scan yet. Click the **'🔄 Run Scraper Now'** button in the sidebar to fetch your first batch of sponsored jobs!")
