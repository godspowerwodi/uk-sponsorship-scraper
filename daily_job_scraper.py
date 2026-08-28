import os
import csv
import json
import requests
from datetime import datetime

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
TARGET_TERMS = ['data engineer', 'data engineering', 'analytics engineer']
TARGET_LOCATIONS = ['london', 'uk', 'united kingdom', 'remote - uk', 'hybrid']

# Large list of ATS companies to check
COMPANIES = [
    "monzo", "revolut", "thoughtworks", "gigs", "coreweave", "wise", "checkout", 
    "elixirr", "plaid", "stripe", "roblox", "discord", "airbnb", "canva", "notion", 
    "figma", "github", "gitlab", "doordash", "instacart", "databricks", "snowflake", 
    "confluent", "hashicorp", "mongodb", "elastic", "affirm", "brex", "ramp", 
    "rippling", "palantir", "datadog", "okta", "crowdstrike", "zscaler", "cloudflare", 
    "twilio", "zoom", "slack", "atlassian", "docusign", "dropbox", "box", "asana", 
    "monday", "smartsheet", "hubspot", "salesforce", "adobe", "autodesk", "unity", 
    "epicgames", "riotgames", "ea", "take2", "activision", "zynga", "tencent", 
    "bytedance", "tiktok", "snap", "pinterest", "twitter", "block", "square", 
    "coinbase", "kraken", "binance", "gemini", "robinhood", "wealthfront", "betterment", 
    "chime", "sofi", "klarna", "adyen", "dlocal", "marqeta", "fivetran", "dbtlabs", 
    "prefect", "dagster", "astronomer", "trino", "starburst", "dremio", "clickhouse", 
    "singlestore", "cockroachlabs", "yugabyte", "planetscale", "neon", "supabase", 
    "vercel", "netlify", "heroku", "digitalocean", "linode", "flyio", "render", 
    "railway", "deliveroo", "spotify", "gusto"
]

def fetch_sponsors():
    """Downloads the official UK Home Office sponsor list and returns a set of lowercase company names."""
    print("Fetching the latest UK Register of Licensed Sponsors CSV...")
    csv_url = "https://assets.publishing.service.gov.uk/media/6a8ff32b5a0c25165ae465cc/SP_-_Worker_and_Temporary_Worker_Web_Register_-_2026-08-27.csv"
    try:
        resp = requests.get(csv_url, timeout=15, verify=False)
        # If the URL changes (it updates daily), we fallback to the landing page to extract it
        if resp.status_code != 200:
            print("Direct link failed, trying to parse HTML for latest CSV...")
            page = requests.get("https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers", timeout=10, verify=False)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                if a['href'].endswith('.csv') and 'Worker_and_Temporary_Worker' in a['href']:
                    csv_url = a['href']
                    if not csv_url.startswith('http'):
                        csv_url = "https://assets.publishing.service.gov.uk" + csv_url
                    resp = requests.get(csv_url, timeout=15, verify=False)
                    break

        sponsors = set()
        decoded_content = resp.content.decode('utf-8-sig')
        reader = csv.reader(decoded_content.splitlines())
        for row in reader:
            if row and len(row) > 0:
                sponsors.add(row[0].strip().lower())
        print(f"Loaded {len(sponsors)} licensed sponsors.")
        return sponsors
    except Exception as e:
        print(f"Error fetching sponsors: {e}")
        return set()

def is_sponsored(company_name, sponsors_set):
    """Checks if a company name exists in the sponsor set."""
    company_norm = company_name.strip().lower()
    if company_norm in sponsors_set:
        return True
    
    # Check partial match for larger entities
    for s in sponsors_set:
        if company_norm in s or s in company_norm:
            # Basic sanity check to avoid matching "and" or short words
            if len(company_norm) > 4 and len(s) > 4:
                return True
    return False

def fetch_jobs(company):
    """Fetches jobs from Greenhouse, Lever, and Ashby APIs."""
    found = []
    # Greenhouse
    try:
        gh = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs", timeout=5)
        if gh.status_code == 200:
            for job in gh.json().get('jobs', []):
                found.append({
                    'title': job.get('title', ''),
                    'location': job.get('location', {}).get('name', ''),
                    'url': job.get('absolute_url', '')
                })
    except: pass
    
    # Lever
    try:
        lv = requests.get(f"https://api.lever.co/v0/postings/{company}", timeout=5)
        if lv.status_code == 200:
            for job in lv.json():
                found.append({
                    'title': job.get('text', ''),
                    'location': job.get('categories', {}).get('location', ''),
                    'url': job.get('hostedUrl', '')
                })
    except: pass

    # Ashby
    try:
        ash = requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{company}", timeout=5)
        if ash.status_code == 200:
            for job in ash.json().get('jobs', []):
                found.append({
                    'title': job.get('title', ''),
                    'location': job.get('location', ''),
                    'url': job.get('url', '')
                })
    except: pass
    
    return found

def send_discord_webhook(jobs):
    if not DISCORD_WEBHOOK_URL:
        print("No Discord Webhook URL provided. Skipping notification.")
        return

    for job in jobs:
        embed = {
            "title": f"🚀 New Sponsored Role: {job['company']} - {job['title']}",
            "description": f"**Location:** {job['location']}\n**Company:** {job['company']}\n\n[Apply Here]({job['url']})",
            "color": 5814783,
            "footer": {"text": "UK Sponsorship Job Validator"}
        }
        
        data = {
            "content": "<@&123456789> A new Data Engineer role with UK Visa Sponsorship was found!" if len(jobs) > 0 else "", # Modify ping if needed
            "embeds": [embed]
        }
        
        try:
            requests.post(DISCORD_WEBHOOK_URL, json=data)
        except Exception as e:
            print(f"Error sending to Discord: {e}")

def update_markdown(jobs):
    file_path = "daily_jobs.md"
    mode = "a" if os.path.exists(file_path) else "w"
    
    with open(file_path, mode, encoding='utf-8') as f:
        if mode == "w":
            f.write("# Daily UK Sponsorship Job Alerts\n\n")
            
        if jobs:
            f.write(f"## New Jobs Found on {datetime.now().strftime('%Y-%m-%d')}\n\n")
            for job in jobs:
                f.write(f"- **{job['company']}**: [{job['title']}]({job['url']}) - *{job['location']}*\n")
            f.write("\n")

def main():
    sponsors = fetch_sponsors()
    if not sponsors:
        print("Could not load sponsors. Exiting.")
        return

    # Load history to avoid duplicate notifications
    history_file = "history.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = set(json.load(f))
    else:
        history = set()

    new_jobs = []

    print("Checking ATS APIs for open roles...")
    for company in COMPANIES:
        jobs = fetch_jobs(company)
        for job in jobs:
            title = job['title'].lower()
            loc = job['location'].lower()
            url = job['url']
            
            # Filter by role and location
            matches_title = any(term in title for term in TARGET_TERMS)
            matches_loc = any(l in loc for l in TARGET_LOCATIONS)
            
            if matches_title and matches_loc:
                if is_sponsored(company, sponsors):
                    if url not in history:
                        print(f"[NEW SPONSORED JOB] {company} - {job['title']}")
                        new_jobs.append({
                            'company': company.title(),
                            'title': job['title'],
                            'location': job['location'],
                            'url': url
                        })
                        history.add(url)
                    else:
                        print(f"[ALREADY SEEN] {company} - {job['title']}")

    if new_jobs:
        send_discord_webhook(new_jobs)
        update_markdown(new_jobs)
        
        # Save history
        with open(history_file, "w") as f:
            json.dump(list(history), f)
        print(f"Successfully processed {len(new_jobs)} new jobs.")
    else:
        print("No new sponsored jobs found today.")

if __name__ == "__main__":
    main()
