import streamlit as st
import asyncio
import pandas as pd
from sponsorship_scout.core.uk_sponsors import fetch_sponsors_and_generate_tenants, is_sponsored
from sponsorship_scout.core.engine import scan_companies

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # Fallback for when an event loop is already running in this thread
        import threading
        result = []
        def _run():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            result.append(new_loop.run_until_complete(coro))
        t = threading.Thread(target=_run)
        t.start()
        t.join()
        return result[0]
    else:
        return loop.run_until_complete(coro)

st.set_page_config(page_title="UK Sponsorship Job Scout", layout="wide", page_icon="🔍")
st.title("🔍 UK Sponsorship Job Scout")
st.markdown("Scan for live jobs from UK companies that offer visa sponsorship, straight from ATS platforms.")

with st.sidebar:
    st.header("🎯 Search Criteria")
    job_title = st.text_input("Job Title Keywords", "Data Engineer", help="Comma-separated keywords for job titles.")
    location = st.text_input("Location", "London", help="Comma-separated locations.")
    industry_keywords = st.text_input("Industry Keywords", "tech, software, data", help="Used to match companies to the UK Gov Sponsor List.")
    scan_button = st.button("🚀 Scan for Sponsored Jobs", type="primary", use_container_width=True)

if scan_button:
    titles = [t.strip().lower() for t in job_title.split(",") if t.strip()]
    locs = [l.strip().lower() for l in location.split(",") if l.strip()]
    industries = set(i.strip().lower() for i in industry_keywords.split(",") if i.strip())
    
    with st.spinner("Scraping ATS platforms... this may take 1-2 minutes."):
        sponsors, tenant_ids = fetch_sponsors_and_generate_tenants(industries)
        
        if not sponsors:
            st.error("Failed to fetch the UK Gov sponsor list.")
            all_jobs = []
        else:
            st.info(f"Loaded **{len(sponsors)}** licensed sponsors and targeting **{len(tenant_ids)}** ATS tenants.")
            all_jobs = run_async(scan_companies(tenant_ids))
            
    if sponsors:
        new_jobs = []
        for job in all_jobs:
            title_lower = job.get('title', '').lower()
            loc_lower = job.get('location', '').lower()
            company = job.get('company', '')
            
            matches_title = any(term in title_lower for term in titles) if titles else True
            matches_loc = any(l in loc_lower for l in locs) if locs else True
            
            if matches_title and matches_loc:
                if is_sponsored(company, sponsors):
                    new_jobs.append(job)
        
        if new_jobs:
            st.success(f"Found {len(new_jobs)} sponsored jobs!")
            df = pd.DataFrame(new_jobs)
            cols = ['company', 'title', 'location', 'url', 'added_date']
            existing_cols = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
            df = df[existing_cols]
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Sponsored Jobs", len(df))
            with col2:
                st.metric("Unique Companies", df['company'].nunique())
                
            st.dataframe(
                df, 
                use_container_width=True, 
                column_config={"url": st.column_config.LinkColumn("Apply Link")},
                hide_index=True
            )
        else:
            st.warning("No sponsored jobs found matching your criteria.")
