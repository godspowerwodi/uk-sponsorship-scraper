import asyncio
import aiohttp
import os
import json
from datetime import datetime
from typing import List, Dict, Set

from .config import Config, Profile, DestinationType, DiscordDestination, GistDestination, SqliteDestination
from .uk_sponsors import fetch_sponsors_and_generate_tenants, is_sponsored
from ..ats import ALL_SCRAPERS
from ..destinations import send_to_discord, send_to_gist, send_to_sqlite

async def fetch_with_sem(func, session, company, sem):
    async with sem:
        return await func(session, company)

async def scan_companies(tenant_ids: Set[str]) -> List[Dict]:
    print(f"Scanning {len(tenant_ids)} companies asynchronously across {len(ALL_SCRAPERS)} ATS platforms...")
    sem = asyncio.Semaphore(20)
    connector = aiohttp.TCPConnector(limit=20) 
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = []
        for company in tenant_ids:
            for scraper in ALL_SCRAPERS:
                tasks.append(fetch_with_sem(scraper, session, company, sem))
        results = await asyncio.gather(*tasks)
        
    all_jobs = []
    for company, jobs in results:
        for job in jobs:
            job['company'] = company
            job['added_date'] = datetime.now().strftime('%Y-%m-%d')
            all_jobs.append(job)
            
    print(f"Scanned {len(results)} endpoints. Found {len(all_jobs)} total jobs.")
    return all_jobs

def process_destinations(jobs: List[Dict], profile: Profile):
    for dest in profile.destinations:
        if isinstance(dest, DiscordDestination):
            send_to_discord(jobs, dest.webhook_url)
        elif isinstance(dest, GistDestination):
            send_to_gist(jobs, dest.gist_id, dest.github_token, f"queue_{profile.name.lower()}.json")
        elif isinstance(dest, SqliteDestination):
            send_to_sqlite(jobs, dest.table_name)

async def run_engine(config: Config):
    master_keywords = set()
    for profile in config.profiles:
        for kw in profile.industry_keywords:
            master_keywords.add(kw.lower())
            
    if not master_keywords:
        master_keywords = {'tech', 'software', 'data', 'cloud'}
        
    sponsors, tenant_ids = fetch_sponsors_and_generate_tenants(master_keywords)
    if not sponsors: return
    
    all_jobs = await scan_companies(tenant_ids)
    
    for profile in config.profiles:
        print(f"--- Processing jobs for user: {profile.name} ---")
        
        history_file = f"history_{profile.name.lower()}.json"
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = set(json.load(f))
        else:
            history = set()

        new_jobs = []
        for job in all_jobs:
            title = job['title'].lower()
            loc = job['location'].lower()
            url = job['url']
            company = job['company']
            
            matches_title = any(term in title for term in profile.target_terms)
            matches_loc = any(l in loc for l in profile.target_locations)
            
            if matches_title and matches_loc:
                if is_sponsored(company, sponsors):
                    if url not in history:
                        print(f"[{profile.name}] Found: {company} - {job['title']}")
                        new_jobs.append(job)
                        history.add(url)
                        
        if new_jobs:
            process_destinations(new_jobs, profile)
            with open(history_file, "w") as f:
                json.dump(list(history), f)
            print(f"[{profile.name}] Processed {len(new_jobs)} new jobs.\n")
        else:
            print(f"[{profile.name}] No new jobs today.\n")
