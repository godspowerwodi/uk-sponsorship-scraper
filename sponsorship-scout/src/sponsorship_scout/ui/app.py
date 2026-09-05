import streamlit as st
import sqlite3
import pandas as pd
import os
import yaml

st.set_page_config(page_title="Sponsorship Scout", layout="wide")
st.title("?? Sponsorship Scout Dashboard")

config_path = os.environ.get('SPONSOR_SCOUT_CONFIG', 'config.yaml')
try:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
except Exception as e:
    st.error(f"Could not load config: {e}")
    st.stop()

# Find SQLite destinations in config
sqlite_tables = []
for profile in config.get('profiles', []):
    for dest in profile.get('destinations', []):
        if dest.get('type') == 'sqlite':
            sqlite_tables.append((profile['name'], dest['table_name']))

if not sqlite_tables:
    st.warning("No SQLite destinations configured in your profiles. Add one to view jobs here!")
    st.stop()

# Select profile to view
profile_name, table_name = st.selectbox("Select Profile", sqlite_tables, format_func=lambda x: x[0])

# Connect to DB
try:
    conn = sqlite3.connect('sponsorship_scout.db')
    df = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY added_date DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("No jobs found in the database yet. Run the scraper!")
    else:
        st.subheader(f"Latest Jobs for {profile_name}")
        st.dataframe(
            df[['added_date', 'company', 'title', 'location', 'url']], 
            use_container_width=True,
            column_config={
                "url": st.column_config.LinkColumn("Apply Link")
            }
        )
except Exception as e:
    st.info(f"Database table '{table_name}' not created yet. Run the scraper first!")
