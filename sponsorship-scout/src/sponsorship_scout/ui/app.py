import streamlit as st
import sqlite3
import pandas as pd
import os
import yaml
import asyncio
from sponsorship_scout.core.config import load_config
from sponsorship_scout.core.engine import run_engine

st.set_page_config(page_title="Sponsorship Scout", layout="wide")
st.title("Sponsorship Scout Dashboard")

config_path = os.environ.get('SPONSOR_SCOUT_CONFIG', 'config.yaml')
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
except Exception as e:
    st.error(f"Could not load config: {e}")
    st.stop()

sqlite_tables = []
for profile in config.get('profiles', []):
    for dest in profile.get('destinations', []):
        if dest.get('type') == 'sqlite':
            sqlite_tables.append((profile['name'], dest['table_name']))

if not sqlite_tables:
    st.warning("No SQLite destinations configured in your profiles. Add one to view jobs here!")
    st.stop()

profile_name, table_name = st.selectbox("Select Profile", sqlite_tables, format_func=lambda x: x[0])

# Add a sidebar button to run the scraper directly from the UI
with st.sidebar:
    st.header("Actions")
    if st.button("🔄 Run Scraper Now"):
        with st.spinner("Scraping ATS platforms... This may take a couple of minutes."):
            cfg = load_config(config_path)
            asyncio.run(run_engine(cfg))
        st.success("Scraping complete! Refreshing data...")
        st.rerun()

try:
    conn = sqlite3.connect('sponsorship_scout.db')
    df = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY added_date DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("No jobs found in the database yet. Click 'Run Scraper Now' in the sidebar to get started!")
    else:
        st.subheader(f"Latest Jobs for {profile_name} ({len(df)} found)")
        st.dataframe(
            df[['added_date', 'company', 'title', 'location', 'url']], 
            use_container_width=True,
            column_config={"url": st.column_config.LinkColumn("Apply Link")}
        )
except Exception:
    st.info("👋 **Welcome to Sponsorship Scout!**\n\nYour database is currently empty because you haven't run a scan yet. Click the **'🔄 Run Scraper Now'** button in the sidebar to fetch your first batch of sponsored jobs!")
