import os
import csv
import json
import asyncio
import aiohttp
import requests
import urllib3
import re
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
TARGET_TERMS = ['data engineer', 'data engineering', 'analytics engineer']
TARGET_LOCATIONS = ['london', 'uk', 'united kingdom', 'remote uk', 'uk remote', 'hybrid - uk']

# Keywords to filter the official sponsor list for tech companies
TECH_KEYWORDS = [
    'tech', 'software', 'data', 'cloud', 'digital', 'analytic', 
    'ai', 'machine learning', 'fintech', 'cyber', 'system', 'network'
]

def load_manual_companies():
    """Loads companies from companies.txt if it exists."""
    companies = set()
    if os.path.exists("companies.txt"):
        with open("companies.txt", "r", encoding="utf-8") as f:
            for line in f:
                c = line.strip().lower()
                if c: companies.add(c)
    return companies

def fetch_sponsors_and_generate_tenants():
    """
    Downloads the UK Home Office sponsor list.
    Returns:
    1. A set of raw sponsor names (for validation).
    2. A set of generated ATS tenant IDs (by filtering tech companies and cleaning names).
    """
    print("Fetching the latest UK Register of Licensed Sponsors CSV...")
    csv_url = "https://assets.publishing.service.gov.uk/media/6a8ff32b5a0c25165ae465cc/SP_-_Worker_and_Temporary_Worker_Web_Register_-_2026-08-27.csv"
    
    try:
        resp = requests.get(csv_url, timeout=15, verify=False)
        if resp.status_code != 200:
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
        tenant_ids = set()
        
        decoded_content = resp.content.decode('utf-8-sig')
        reader = csv.reader(decoded_content.splitlines())
        
        for row in reader:
            if row and len(row) > 0:
                raw_name = row[0].strip().lower()
                sponsors.add(raw_name)
                
                # Check if it's a tech company
                if any(kw in raw_name for kw in TECH_KEYWORDS):
                    # Clean the name to guess the ATS tenant ID
                    # e.g. "Deliveroo Ltd" -> "deliveroo"
                    clean_name = raw_name.replace(" ltd", "").replace(" limited", "").replace(" uk", "")
                    clean_name = re.sub(r'[^a-z0-9]', '', clean_name)
                    if len(clean_name) > 3:
                        tenant_ids.add(clean_name)
                        
        print(f"Loaded {len(sponsors)} licensed sponsors.")
        print(f"Generated {len(tenant_ids)} potential tech ATS tenant IDs.")
        return sponsors, tenant_ids
        
    except Exception as e:
        print(f"Error fetching sponsors: {e}")
        return set(), set()

def is_sponsored(company_name, sponsors_set):
    company_norm = company_name.strip().lower()
    if company_norm in sponsors_set:
        return True
    for s in sponsors_set:
        if company_norm in s or s in company_norm:
            if len(company_norm) > 4 and len(s) > 4:
                return True
    return False

async def fetch_greenhouse(session, company):
    try:
        async with session.get(f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs", timeout=5, ssl=False) as resp:
            if resp.status == 200:
                data = await resp.json()
                return company, [{'title': j.get('title',''), 'location': j.get('location',{}).get('name',''), 'url': j.get('absolute_url','')} for j in data.get('jobs', [])]
    except: pass
    return company, []

async def fetch_lever(session, company):
    try:
        async with session.get(f"https://api.lever.co/v0/postings/{company}", timeout=5, ssl=False) as resp:
            if resp.status == 200:
                data = await resp.json()
                return company, [{'title': j.get('text',''), 'location': j.get('categories',{}).get('location',''), 'url': j.get('hostedUrl','')} for j in data]
    except: pass
    return company, []

async def fetch_ashby(session, company):
    try:
        async with session.get(f"https://api.ashbyhq.com/posting-api/job-board/{company}", timeout=5, ssl=False) as resp:
            if resp.status == 200:
                data = await resp.json()
                return company, [{'title': j.get('title',''), 'location': j.get('location',''), 'url': j.get('url','')} for j in data.get('jobs', [])]
    except: pass
    return company, []

async def scan_companies(tenant_ids):
    print(f"Scanning {len(tenant_ids)} companies asynchronously...")
    connector = aiohttp.TCPConnector(limit=50) # Limit concurrent connections
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for company in tenant_ids:
            tasks.append(fetch_greenhouse(session, company))
            tasks.append(fetch_lever(session, company))
            tasks.append(fetch_ashby(session, company))
        
        results = await asyncio.gather(*tasks)
        
    # Flatten results
    all_jobs = []
    for company, jobs in results:
        for job in jobs:
            job['company'] = company
            all_jobs.append(job)
            
    print(f"Scanned {len(results)} endpoints. Found {len(all_jobs)} total tech jobs.")
    return all_jobs

def send_discord_webhook(jobs):
    if not DISCORD_WEBHOOK_URL:
        print("No Discord Webhook URL provided. Skipping notification.")
        return

    for job in jobs:
        embed = {
            "title": f"🚀 New Sponsored Role: {job['company']} - {job['title']}",
            "description": f"**Location:** {job['location']}\n**Company:** {job['company'].title()}\n\n[Apply Here]({job['url']})",
            "color": 5814783,
            "footer": {"text": "UK Sponsorship Job Validator"}
        }
        
        data = {
            "content": "<@&123456789> A new Data Engineer role with UK Visa Sponsorship was found!" if len(jobs) > 0 else "", 
            "embeds": [embed]
        }
        
        try:
            requests.post(DISCORD_WEBHOOK_URL, json=data, verify=False)
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
                f.write(f"- **{job['company'].title()}**: [{job['title']}]({job['url']}) - *{job['location']}*\n")
            f.write("\n")

def update_queue(jobs):
    file_path = "pending_applications.json"
    queue = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                queue = json.load(f)
        except:
            pass
            
    # Avoid adding duplicates to the queue just in case
    existing_urls = {j['url'] for j in queue}
    for job in jobs:
        if job['url'] not in existing_urls:
            queue.append({
                "company": job['company'].title(),
                "title": job['title'],
                "location": job['location'],
                "url": job['url'],
                "added_date": datetime.now().strftime('%Y-%m-%d')
            })
            
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(queue, f, indent=4)

async def main():
    sponsors, generated_tenants = fetch_sponsors_and_generate_tenants()
    if not sponsors: return

    manual_tenants = load_manual_companies()
    all_tenants = generated_tenants.union(manual_tenants)
    
    # Run async scan
    all_jobs = await scan_companies(all_tenants)

    # Load history
    history_file = "history.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = set(json.load(f))
    else:
        history = set()

    new_jobs = []

    print("Filtering for Target Roles & Sponsorship...")
    for job in all_jobs:
        title = job['title'].lower()
        loc = job['location'].lower()
        url = job['url']
        company = job['company']
        
        matches_title = any(term in title for term in TARGET_TERMS)
        matches_loc = any(l in loc for l in TARGET_LOCATIONS)
        
        if matches_title and matches_loc:
            # We already know manual ones are fine, but generated ones MUST be in sponsor list
            if is_sponsored(company, sponsors) or company in manual_tenants:
                if url not in history:
                    print(f"[NEW SPONSORED JOB] {company} - {job['title']}")
                    new_jobs.append(job)
                    history.add(url)

    if new_jobs:
        send_discord_webhook(new_jobs)
        update_markdown(new_jobs)
        update_queue(new_jobs)
        
        with open(history_file, "w") as f:
            json.dump(list(history), f)
        print(f"Successfully processed {len(new_jobs)} new jobs.")
    else:
        print("No new sponsored jobs found today.")

if __name__ == "__main__":
    asyncio.run(main())
