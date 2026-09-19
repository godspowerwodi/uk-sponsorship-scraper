import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="UK Sponsorship Job Scout", layout="wide", page_icon="💼")

st.markdown("""

<style>
/* Hide Streamlit header (hamburger menu) and footer (watermark) */
header {visibility: hidden !important;}
footer {visibility: hidden !important;}
/* Hide full screen button just in case */
button[title="View fullscreen"] {display: none !important;}

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
/* Primary button custom color (ToolzHub blue) */
.stButton button[kind="primary"],
.stButton button[data-testid="baseButton-primary"],
.stButton button[data-testid="stBaseButton-primary"] {
    background-color: #4f46e5 !important;
    color: white !important;
    border: none !important;
}
.stButton button[kind="primary"]:hover,
.stButton button[data-testid="baseButton-primary"]:hover,
.stButton button[data-testid="stBaseButton-primary"]:hover {
    background-color: #4338ca !important;
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

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_jobs_from_db():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        return []
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(supabase_url, supabase_key)
        jobs = []
        page_size = 1000
        offset = 0
        while True:
            response = supabase.table("jobs").select("id, title, company, location, url, salary, visa_routes, created_at").range(offset, offset + page_size - 1).execute()
            if not response.data:
                break
            jobs.extend(response.data)
            if len(response.data) < page_size:
                break
            offset += page_size
        return jobs
    except Exception as e:
        print(f"Failed to fetch jobs: {e}")
        return []

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

col1, col2, col3, col4 = st.columns(4)
with col1:
    job_title = st.text_input("Job Title Keywords", "Data Engineer", help="Comma-separated keywords for job titles.")
with col2:
    location = st.text_input("Location", "London", help="Comma-separated locations.")
with col3:
    role_level = st.selectbox("Role Level", ["Any", "Junior / Entry", "Mid Level", "Senior / Lead", "Director / Exec"])
with col4:
    salary_threshold = st.selectbox("Salary Threshold", ["Any", "Meets Threshold or Unknown", "Strictly Meets Threshold"])

cv_text = st.text_area("Paste your CV (Optional for ATS Match)", help="Paste your CV text to get a match score against full job descriptions.", max_chars=50000)
st.caption("This runs a strict ATS keyword algorithm against the full job description.")
st.markdown("<p style='font-size: 11px; color: #888; margin-top: -10px;'>(Your CV is temporarily securely stored for 24 hours to enable cross-platform AI ATS Optimization, after which it is permanently deleted. We do not sell or use this data for any other purpose. For peace of mind, feel free to omit your name and contact info before pasting.)</p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
with btn_col2:
    scan_button = st.button("🚀 Find Sponsored Jobs", type="primary", width="stretch")
st.divider()

if scan_button:
    with st.spinner("🚀 Searching database and analyzing CV..."):
        if 0 < len(cv_text.strip()) < 300:
            cv_text = ""
            st.warning("⚠️ The text provided is too short to be a valid CV. Proceeding with standard job search without ATS scoring.")
        
        titles = [t.strip().lower() for t in job_title.split(",") if t.strip()]
        locs = [l.strip().lower() for l in location.split(",") if l.strip()]
    
        all_jobs = fetch_all_jobs_from_db()
        if not all_jobs:
            if not os.environ.get("SUPABASE_URL"):
                st.error("Database connection missing. Please configure SUPABASE_URL and SUPABASE_KEY.")
            else:
                st.error("Failed to fetch jobs or database is empty.")
        else:
            st.info(f"Loaded **{len(all_jobs)}** sponsored jobs from the database.")

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
                
                    matches_salary = True
                    if salary_threshold == "Strictly Meets Threshold":
                        matches_salary = job['Salary Check'] == '🟢 Green'
                    elif salary_threshold == "Meets Threshold or Unknown":
                        matches_salary = job['Salary Check'] in ['🟢 Green', '🟠 Amber']
                
                    if matches_salary:
                        job['routes'] = job.get('visa_routes', 'Unknown')
                        new_jobs.append(job)
        
            if new_jobs:
                if cv_text.strip():
                    try:
                        from sklearn.feature_extraction.text import CountVectorizer
                        base_stops = list(CountVectorizer(stop_words='english').get_stop_words())
                        custom_stops = base_stops + ['experience', 'team', 'role', 'work', 'working', 'company', 'skills', 'looking', 'years', 'business', 'using', 'new', 'support', 'including', 'development', 'opportunity', 'join', 'strong', 'knowledge', 'good', 'ability', 'required', 'excellent', 'ensure', 'help', 'provide', 'understanding', 'design', 'building', 'based', 'time', 'people', 'environment', 'learning', 'best', 'solutions', 'project', 'projects', 'within', 'across', 'key', 'day', 'will']
                        cv_lower = cv_text.lower()
                    
                        # LAZY FETCH DESCRIPTIONS FOR MATCHED JOBS ONLY
                        job_ids = [j['id'] for j in new_jobs if 'id' in j]
                        descriptions_map = {}
                        cv_uuid = ""
                        if job_ids:
                            supabase_url = os.environ.get("SUPABASE_URL")
                            supabase_key = os.environ.get("SUPABASE_KEY")
                            if supabase_url and supabase_key:
                                from supabase import create_client, Client
                                import concurrent.futures
                                supabase: Client = create_client(supabase_url, supabase_key)
                            
                                try:
                                    cv_insert = supabase.table("temp_cvs").insert({"cv_text": cv_text.strip()}).execute()
                                    if cv_insert.data:
                                        cv_uuid = cv_insert.data[0].get("id", "")
                                except Exception as e:
                                    st.warning(f"Failed to store CV temporarily: {e}")
                                
                                def fetch_chunk(chunk):
                                    results = []
                                    try:
                                        # Split the 300-item chunk internally into 150-item sub-chunks 
                                        # to avoid hitting Kong's 8KB URI limit with 300 UUIDs (~11KB)
                                        for i in range(0, len(chunk), 150):
                                            sub_chunk = chunk[i:i+150]
                                            resp = supabase.table("jobs").select("id, description").in_("id", sub_chunk).execute()
                                            if resp.data:
                                                results.extend(resp.data)
                                        return results
                                    except Exception as e:
                                        print(f"Failed to fetch chunk: {e}")
                                        return []

                                chunks = [job_ids[i:i+300] for i in range(0, len(job_ids), 300)]
                                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                                    futures = [executor.submit(fetch_chunk, c) for c in chunks]
                                    for future in concurrent.futures.as_completed(futures):
                                        for row in future.result():
                                            descriptions_map[row['id']] = row.get('description', '')

                        for job in new_jobs:
                            jd_text = str(descriptions_map.get(job.get('id'), job.get('title')) or job.get('title') or '')
                            try:
                                vec = CountVectorizer(stop_words=custom_stops, ngram_range=(1, 2), max_features=30)
                                vec.fit([jd_text])
                                keywords = vec.get_feature_names_out()
                                matches = sum(1 for kw in keywords if re.search(rf'\b{re.escape(kw)}\b', cv_lower))
                                score = (matches / len(keywords)) * 100 if len(keywords) > 0 else 0.0
                            except ValueError:
                                score = 0.0
                            
                            job['CV Match Score'] = f"{score:.1f}%"
                            job['_raw_score'] = score
                            if score >= 95:
                                job['ATS Status'] = "✅ Strong Match"
                            else:
                                job['ATS Status'] = "⚠️ Low Score (Fails ATS)"
                            if score < 95:
                                import urllib.parse
                                encoded_url = urllib.parse.quote_plus(job.get('url') or '')
                                job['Boost ATS Score'] = f"https://tinytoolz-hub.onrender.com/ats-matcher?utm_source=sponsorship_scout_table&cv_id={cv_uuid}&job_url={encoded_url}"
                            else:
                                job['Boost ATS Score'] = None
                        
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
                    cols = ['company', 'title', 'location', 'url', 'salary', 'Salary Check', 'CV Match Score', 'ATS Status', 'Boost ATS Score', 'routes', 'created_at']
                    df_exact = df_exact[[c for c in cols if c in df_exact.columns] + [c for c in df_exact.columns if c not in cols and c not in ('description', '_raw_score', 'id', 'visa_routes')]]
                
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Exact Matches", len(df_exact))
                    with col2:
                        st.metric("Unique Companies", df_exact['company'].nunique())
                    
                    if 'ATS Status' in df_exact.columns and (df_exact['ATS Status'] == "⚠️ Low Score (Fails ATS)").any():
                        st.error("🚨 **Your CV is failing the automated ATS screen for some of these jobs.** Your resume is missing critical keywords. Companies use Applicant Tracking Systems to automatically reject CVs that don't match the Job Description. 👉 **Click the '⚠️ Optimize CV' link in the table below to have our AI automatically rewrite your CV for that specific role.**")
                    
                    st.dataframe(df_exact, use_container_width=True, column_config={"url": st.column_config.LinkColumn("Apply Link"), "Boost ATS Score": st.column_config.LinkColumn("Boost ATS Score", display_text="⚠️ Optimize CV")}, hide_index=True)
                else:
                    st.warning("We couldn't find an exact match for your search, but here are other roles like it:")
                
                if broader_matches:
                    if exact_matches:
                        st.info(f"Found {len(broader_matches)} broader matches similar to your search:")
                    df_broad = pd.DataFrame(broader_matches)
                    cols = ['company', 'title', 'location', 'url', 'salary', 'Salary Check', 'CV Match Score', 'ATS Status', 'Boost ATS Score', 'routes', 'created_at']
                    df_broad = df_broad[[c for c in cols if c in df_broad.columns] + [c for c in df_broad.columns if c not in cols and c not in ('description', '_raw_score', 'id', 'visa_routes')]]
                
                    if 'ATS Status' in df_broad.columns and (df_broad['ATS Status'] == "⚠️ Low Score (Fails ATS)").any():
                        st.error("🚨 **Your CV is failing the automated ATS screen for some of these jobs.** Your resume is missing critical keywords. Companies use Applicant Tracking Systems to automatically reject CVs that don't match the Job Description. 👉 **Click the '⚠️ Optimize CV' link in the table below to have our AI automatically rewrite your CV for that specific role.**")
                    
                    st.dataframe(df_broad, use_container_width=True, column_config={"url": st.column_config.LinkColumn("Apply Link"), "Boost ATS Score": st.column_config.LinkColumn("Boost ATS Score", display_text="⚠️ Optimize CV")}, hide_index=True)
            else:
                st.warning("No sponsored jobs found matching your criteria.")

    components.html(
        """
        <script>
        const df = window.parent.document.querySelector('.stDataFrame, [data-testid="stDataFrame"]');
        if(df) {
            df.scrollIntoView({behavior: 'smooth', block: 'start'});
        }
        </script>
        """,
        height=0
    )

st.markdown(
    """
    <div style="background-color: #f5f5f7; padding: 40px 20px; border-radius: 16px; margin-top: 40px; text-align: center;">
        <p style="margin-bottom: 8px; color: #86868b; font-size: 14px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">See other toolz built by me</p>
        <h3 style="margin-bottom: 16px; color: #1d1d1f; font-size: 28px; font-weight: 600; letter-spacing: -0.01em;">AI shortcuts for everyday internet hiccups.</h3>
        <p style="margin-bottom: 24px; color: #515154; font-size: 17px; line-height: 1.5; max-width: 500px; margin-left: auto; margin-right: auto;">
            Meet <b>TinyToolz</b>. A constantly expanding ecosystem of AI-powered micro-tools designed to remove digital friction from your day. From bypassing news paywalls to transforming complex web tables into pristine spreadsheets—we build cheat codes for the modern web.
        </p>
        <a href="https://tinytoolzhub.org/?utm_source=sponsorship_scouter" target="_blank" style="display: inline-block; background-color: #4f46e5; color: white; padding: 12px 24px; border-radius: 980px; text-decoration: none; font-weight: 400; font-size: 16px; transition: all 0.3s ease;">Explore TinyToolz</a>
    </div>
    <div style="height: 65px;"></div>
    """,
    unsafe_allow_html=True
)
