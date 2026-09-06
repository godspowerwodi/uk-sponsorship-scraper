import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import asyncio
import pandas as pd
from sponsorship_scout.core.uk_sponsors import fetch_sponsors_and_generate_tenants, is_sponsored
from sponsorship_scout.core.engine import scan_companies

def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        # Fallback for when an event loop is already running in this thread
        import threading
        result = []
        def _run():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            result.append(new_loop.run_until_complete(coro))
            new_loop.close()
        t = threading.Thread(target=_run)
        t.start()
        t.join()
        return result[0]
    else:
        return asyncio.run(coro)

st.set_page_config(page_title="UK Sponsorship Job Scout", layout="wide", page_icon="💼")

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

st.title("💼 UK Sponsorship Job Scout")
st.markdown("Scan for live jobs from UK companies that offer visa sponsorship, straight from ATS platforms.")

st.divider()

# Mobile-friendly Search Inputs (moved out of sidebar so they are immediately visible on small screens)
st.subheader("🎯 Search Criteria")

# Use columns for a better layout on desktop; on mobile, Streamlit automatically stacks them vertically!
col1, col2, col3 = st.columns(3)
with col1:
    job_title = st.text_input("Job Title Keywords", "Data Engineer", help="Comma-separated keywords for job titles.")
with col2:
    location = st.text_input("Location", "London", help="Comma-separated locations.")
with col3:
    industry_keywords = st.text_input("Industry Keywords", "tech, software, data", help="Used to match companies to the UK Gov Sponsor List.")

st.markdown("<br>", unsafe_allow_html=True)
btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
with btn_col2:
    scan_button = st.button("🚀 Scan for Sponsored Jobs", type="primary", width="stretch")
st.divider()

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
            all_jobs = run_async(scan_companies(tenant_ids, titles))
            
    if sponsors:
        # Pre-load UK terms if a broad UK search is requested
        broad_uk_terms = {"uk", "gb", "united kingdom"}
        user_searched_broad_loc = any(l in broad_uk_terms for l in locs) if locs else False
        uk_terms = set()
        if user_searched_broad_loc:
            import geonamescache
            gc = geonamescache.GeonamesCache()
            cities = gc.get_cities()
            uk_cities = {city['name'].lower() for city in cities.values() if city['countrycode'] == 'GB'}
            uk_terms = uk_cities.union({"uk", "united kingdom", "gb", "england", "scotland", "wales", "northern ireland"})
            
        new_jobs = []
        for job in all_jobs:
            title_lower = job.get('title', '').lower()
            loc_lower = job.get('location', '').lower()
            company = job.get('company', '')
            
            matches_title = True
            if titles:
                from rapidfuzz import fuzz
                matches_title = any(fuzz.partial_ratio(term, title_lower) > 75 or fuzz.token_set_ratio(term, title_lower) > 75 for term in titles)
                
            matches_loc = True
            if locs:
                # NHS checks
                is_nhs = False
                url_lower = (job.get('url') or '').lower()
                company_lower = company.lower()
                if "jobs.nhs.uk" in url_lower or "nhs" in company_lower:
                    is_nhs = True
                
                if is_nhs:
                    matches_loc = True
                else:
                    if user_searched_broad_loc:
                        loc_parts = set(loc_lower.replace(',', ' ').split())
                        matches_loc = bool(loc_parts.intersection(uk_terms))
                    else:
                        from rapidfuzz import fuzz
                        matches_loc = any(fuzz.partial_ratio(l, loc_lower) > 75 or fuzz.token_set_ratio(l, loc_lower) > 75 for l in locs)
            
            if matches_title and matches_loc:
                if is_sponsored(company, sponsors):
                    new_jobs.append(job)
        
        if new_jobs:
            exact_matches = []
            broader_matches = []
            for job in new_jobs:
                title_lower = job.get('title', '').lower()
                is_exact = any(term in title_lower for term in titles) if titles else True
                if is_exact:
                    exact_matches.append(job)
                else:
                    broader_matches.append(job)
            
            if exact_matches:
                st.success(f"Found {len(exact_matches)} exact matches!")
                import pandas as pd
                df_exact = pd.DataFrame(exact_matches)
                cols = ['company', 'title', 'location', 'url', 'added_date']
                df_exact = df_exact[[c for c in cols if c in df_exact.columns] + [c for c in df_exact.columns if c not in cols]]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Exact Matches", len(df_exact))
                with col2:
                    st.metric("Unique Companies", df_exact['company'].nunique())
                    
                st.dataframe(df_exact, use_container_width=True, column_config={"url": st.column_config.LinkColumn("Apply Link")}, hide_index=True)
            else:
                st.warning("We couldn't find an exact match for your search, but here are other roles like it:")
                
            if broader_matches:
                if exact_matches:
                    st.info(f"Found {len(broader_matches)} broader matches similar to your search:")
                import pandas as pd
                df_broad = pd.DataFrame(broader_matches)
                cols = ['company', 'title', 'location', 'url', 'added_date']
                df_broad = df_broad[[c for c in cols if c in df_broad.columns] + [c for c in df_broad.columns if c not in cols]]
                st.dataframe(df_broad, use_container_width=True, column_config={"url": st.column_config.LinkColumn("Apply Link")}, hide_index=True)
        else:
            st.warning("No sponsored jobs found matching your criteria.")
