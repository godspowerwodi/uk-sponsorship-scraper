import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
from supabase import create_client, Client

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

import re

def parse_salary_and_check(salary_str: str) -> str:
    if not salary_str or not isinstance(salary_str, str):
        return '🟠 Amber'
    nums = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', salary_str)
    if not nums:
        return '🟠 Amber'
    clean_nums = [float(n.replace(',', '')) for n in nums]
    max_sal = max(clean_nums)
    return '🟢 Green' if max_sal >= 41800 else '🔴 Red'

st.title("💼 UK Sponsorship Job Scout")
st.markdown("Scan for live jobs from UK companies that offer visa sponsorship, straight from ATS platforms.")

st.info("**Salary Check Legend**: 🟢 >= £41,800 | 🔴 < £41,800 | 🟠 Missing or Unclear (Depends on experience, hourly rate, etc.)\n\n*Note: We use the standard £41,800 Skilled Worker rate to calculate the salary traffic light. Sponsorship criteria may differ based on your visa type (e.g., Health and Care visas have a much lower threshold).*")

st.divider()

st.subheader("🎯 Search Criteria")

with st.expander("ℹ️ How to use this search", expanded=True):
    st.markdown("""
    **Welcome! Here's how to fill out the search fields:**
    
    * **Job Title Keywords:** Enter comma-separated keywords for the roles you want (e.g., `Data Engineer, Software Developer, Python, Machine Learning Engineer, Carer, Doctor, Nurse`). The search is flexible and will find similar titles.
    * **Location:** Enter your target cities or regions, separated by commas (e.g., `London, Manchester, Bristol`). You can also just enter `UK` for nationwide searches.
    """)

col1, col2, col3 = st.columns(3)
with col1:
    job_title = st.text_input("Job Title Keywords", "Data Engineer", help="Comma-separated keywords for job titles.")
with col2:
    location = st.text_input("Location", "London", help="Comma-separated locations.")
with col3:
    role_level = st.selectbox("Role Level", ["Any", "Junior / Entry", "Mid Level", "Senior / Lead", "Director / Exec"])

cv_text = st.text_area("Paste your CV (Optional for ATS Match)", help="Paste your CV text to get a match score against full job descriptions.")
st.caption("This will calculate a TF-IDF Cosine Similarity match score against the full job description.")

st.markdown("<br>", unsafe_allow_html=True)
btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
with btn_col2:
    scan_button = st.button("🚀 Find Sponsored Jobs", type="primary", width="stretch")
st.divider()

if scan_button:
    titles = [t.strip().lower() for t in job_title.split(",") if t.strip()]
    locs = [l.strip().lower() for l in location.split(",") if l.strip()]
    
    with st.spinner("Fetching live jobs from our database..."):
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            st.error("Database connection missing. Please configure SUPABASE_URL and SUPABASE_KEY.")
            all_jobs = []
        else:
            try:
                supabase: Client = create_client(supabase_url, supabase_key)
                
                all_jobs = []
                page_size = 1000
                offset = 0
                while True:
                    response = supabase.table("jobs").select("*").range(offset, offset + page_size - 1).execute()
                    if not response.data:
                        break
                    all_jobs.extend(response.data)
                    if len(response.data) < page_size:
                        break
                    offset += page_size
                    
                st.info(f"Loaded **{len(all_jobs)}** sponsored jobs from the database.")
            except Exception as e:
                st.error(f"Failed to fetch jobs: {e}")
                all_jobs = []

    if all_jobs:
        broad_uk_terms = {"uk", "gb", "united kingdom"}
        user_searched_broad_loc = any(l in broad_uk_terms for l in locs) if locs else False
        uk_terms = set()
        if user_searched_broad_loc:
            uk_terms = {"uk", "united kingdom", "gb", "england", "scotland", "wales", "northern ireland", "london", "manchester", "birmingham", "leeds", "glasgow", "liverpool", "newcastle", "sheffield", "belfast", "bristol", "edinburgh", "cardiff"}
            
        new_jobs = []
        for job in all_jobs:
            title_lower = str(job.get('title') or '').lower()
            loc_lower = str(job.get('location') or '').lower()
            company = str(job.get('company') or '')
            
            matches_title = True
            if titles:
                from rapidfuzz import fuzz
                matches_title = any(fuzz.partial_ratio(term, title_lower) > 75 or fuzz.token_set_ratio(term, title_lower) > 75 for term in titles)
                
            matches_loc = True
            if locs:
                is_nhs = False
                url_lower = (job.get('url') or '').lower()
                company_lower = company.lower()
                if "jobs.nhs.uk" in url_lower or "nhs" in company_lower:
                    is_nhs = True
                
                if is_nhs and user_searched_broad_loc:
                    matches_loc = True
                else:
                    if user_searched_broad_loc:
                        matches_loc = any(re.search(r'\b' + re.escape(uk_term) + r'\b', loc_lower) for uk_term in uk_terms)
                    else:
                        def _check_loc(user_loc, job_loc):
                            if re.search(r'\b' + re.escape(user_loc) + r'\b', job_loc):
                                if user_loc == 'york' and 'new york' in job_loc:
                                    return False
                                return True
                            return False
                        matches_loc = any(_check_loc(l, loc_lower) for l in locs)
            
            matches_level = True
            if role_level != "Any":
                level_keywords_junior = ["junior", "jr", "entry", "graduate", "trainee", "intern"]
                level_keywords_senior = ["senior", "sr", "lead", "principal", "head", "staff", "manager"]
                level_keywords_director = ["director", "vp", "chief"]
                if role_level == "Junior / Entry":
                    matches_level = any(re.search(rf'\b{re.escape(k)}\b', title_lower) for k in level_keywords_junior)
                elif role_level == "Senior / Lead":
                    matches_level = any(re.search(rf'\b{re.escape(k)}\b', title_lower) for k in level_keywords_senior)
                elif role_level == "Director / Exec":
                    matches_level = any(re.search(rf'\b{re.escape(k)}\b', title_lower) for k in level_keywords_director)
                elif role_level == "Mid Level":
                    matches_level = not any(re.search(rf'\b{re.escape(k)}\b', title_lower) for k in (level_keywords_junior + level_keywords_senior + level_keywords_director))

            if matches_title and matches_loc and matches_level:
                salary = job.get('salary', '')
                job['Salary Check'] = parse_salary_and_check(salary)
                job['routes'] = job.get('visa_routes', 'Unknown')
                new_jobs.append(job)
        
        if new_jobs:
            if cv_text.strip():
                try:
                    from sklearn.feature_extraction.text import TfidfVectorizer
                    from sklearn.metrics.pairwise import cosine_similarity
                    vectorizer = TfidfVectorizer(stop_words='english')
                    
                    descriptions = [cv_text] + [str(j.get('description') or j.get('title') or '') for j in new_jobs]
                    tfidf_matrix = vectorizer.fit_transform(descriptions)
                    
                    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
                    
                    for i, job in enumerate(new_jobs):
                        score = cosine_similarities[i] * 100
                        job['CV Match Score'] = f"{score:.1f}%"
                        job['_raw_score'] = score
                        
                    new_jobs.sort(key=lambda x: x.get('_raw_score', 0), reverse=True)
                except Exception as e:
                    st.warning(f"Could not calculate CV match score: {e}")

            exact_matches = []
            broader_matches = []
            for job in new_jobs:
                title_lower = str(job.get('title') or '').lower()
                is_exact = any(term in title_lower for term in titles) if titles else True
                if is_exact:
                    exact_matches.append(job)
                else:
                    broader_matches.append(job)
            
            if exact_matches:
                st.success(f"Found {len(exact_matches)} exact matches!")
                df_exact = pd.DataFrame(exact_matches)
                cols = ['company', 'title', 'location', 'url', 'routes', 'salary', 'Salary Check', 'CV Match Score', 'created_at']
                df_exact = df_exact[[c for c in cols if c in df_exact.columns] + [c for c in df_exact.columns if c not in cols and c not in ('description', '_raw_score', 'id')]]
                
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
                df_broad = pd.DataFrame(broader_matches)
                cols = ['company', 'title', 'location', 'url', 'routes', 'salary', 'Salary Check', 'CV Match Score', 'created_at']
                df_broad = df_broad[[c for c in cols if c in df_broad.columns] + [c for c in df_broad.columns if c not in cols and c not in ('description', '_raw_score', 'id')]]
                st.dataframe(df_broad, use_container_width=True, column_config={"url": st.column_config.LinkColumn("Apply Link")}, hide_index=True)
        else:
            st.warning("No sponsored jobs found matching your criteria.")

