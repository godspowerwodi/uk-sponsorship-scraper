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
        # Streamlit sometimes runs in an event loop environment (e.g. within some async contexts)
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(coro)
    else:
        return asyncio.run(coro)

st.title("UK Sponsorship Job Scout")
st.write("Scan for live jobs from UK companies that offer visa sponsorship.")

job_title = st.text_input("Job Title Keywords (comma-separated)", "Data Engineer")
location = st.text_input("Location (comma-separated)", "London")
industry_keywords = st.text_input("Industry Keywords (comma-separated)", "tech, software, data")

if st.button("Scan for Sponsored Jobs"):
    with st.spinner("Scraping ATS platforms... this may take 1-2 minutes."):
        titles = [t.strip().lower() for t in job_title.split(",") if t.strip()]
        locs = [l.strip().lower() for l in location.split(",") if l.strip()]
        industries = set(i.strip().lower() for i in industry_keywords.split(",") if i.strip())

        sponsors, tenant_ids = fetch_sponsors_and_generate_tenants(industries)
        
        if not sponsors:
            st.error("Failed to fetch the UK Gov sponsor list.")
        else:
            st.info(f"Loaded {len(sponsors)} licensed sponsors and targeting {len(tenant_ids)} ATS tenants.")
            
            # Use asyncio.run for the async engine
            all_jobs = run_async(scan_companies(tenant_ids))
            
            new_jobs = []
            for job in all_jobs:
                title_lower = job.get('title', '').lower()
                loc_lower = job.get('location', '').lower()
                company = job.get('company', '')
                
                matches_title = any(term in title_lower for term in titles)
                matches_loc = any(l in loc_lower for l in locs) if locs else True
                
                if matches_title and matches_loc:
                    if is_sponsored(company, sponsors):
                        new_jobs.append(job)
            
            if new_jobs:
                st.success(f"Found {len(new_jobs)} sponsored jobs!")
                df = pd.DataFrame(new_jobs)
                # Reorder columns if they exist
                cols = ['company', 'title', 'location', 'url', 'added_date']
                existing_cols = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
                df = df[existing_cols]
                st.dataframe(df)
            else:
                st.warning("No sponsored jobs found matching your criteria.")
