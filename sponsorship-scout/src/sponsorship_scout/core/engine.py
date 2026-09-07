import asyncio
import aiohttp
import os
import json
from datetime import datetime
from typing import List, Dict, Set

from .config import Config, Profile, DestinationType, DiscordDestination, GistDestination, SqliteDestination, SupabaseDestination
from .uk_sponsors import fetch_sponsors_and_generate_tenants, is_sponsored
from ..ats import TENANT_SCRAPERS, CENTRALIZED_SCRAPERS
from ..destinations import send_to_discord, send_to_gist, send_to_sqlite, send_to_supabase

async def fetch_with_sem(func, session, arg, sem):
    async with sem:
        return await func(session, arg)

async def scan_companies(tenant_ids: Set[str], search_terms: List[str] = None) -> List[Dict]:
    search_terms = search_terms or []
    print(f"Scanning {len(tenant_ids)} companies asynchronously across {len(TENANT_SCRAPERS)} ATS platforms and {len(CENTRALIZED_SCRAPERS)} centralized scrapers...")
    sem = asyncio.Semaphore(150)
    connector = aiohttp.TCPConnector(limit=150) 
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = []
        for company in tenant_ids:
            for scraper in TENANT_SCRAPERS:
                tasks.append(fetch_with_sem(scraper, session, company, sem))
        
        if search_terms:
            for scraper in CENTRALIZED_SCRAPERS:
                tasks.append(fetch_with_sem(scraper, session, search_terms, sem))
                
        results = await asyncio.gather(*tasks)
        
    all_jobs = []
    for company, jobs in results:
        for job in jobs:
            job['company'] = job.get('company') or company
            job['added_date'] = datetime.now().strftime('%Y-%m-%d')
            all_jobs.append(job)
            
    print(f"Scanned endpoints. Found {len(all_jobs)} total jobs.")
    return all_jobs

def process_destinations(jobs: List[Dict], profile: Profile):
    for dest in profile.destinations:
        if isinstance(dest, DiscordDestination):
            webhook_url = dest.webhook_url or os.environ.get("DISCORD_WEBHOOK_URL")
            if webhook_url:
                send_to_discord(jobs, webhook_url)
            else:
                print("Warning: Discord destination configured but no webhook_url provided or DISCORD_WEBHOOK_URL env var found.")
        elif isinstance(dest, GistDestination):
            safe_name = "".join(c if c.isalnum() else "_" for c in profile.name.lower())
            send_to_gist(jobs, dest.gist_id, dest.github_token, f"queue_{safe_name}.json")
        elif isinstance(dest, SqliteDestination):
            send_to_sqlite(jobs, dest.table_name)
        elif isinstance(dest, SupabaseDestination):
            send_to_supabase(jobs)

async def run_engine(config: Config, search_terms: List[str] = None):
    if not config.profiles:
        print("No profiles configured. Exiting.")
        return

    master_keywords = set()
    for profile in config.profiles:
        for kw in profile.industry_keywords:
            master_keywords.add(kw.lower())
            
    if not master_keywords:
        master_keywords = {'tech', 'software', 'data', 'cloud'}
        
    sponsors, tenant_ids = fetch_sponsors_and_generate_tenants(master_keywords)
    if not sponsors: return
    
    # If search_terms not passed directly, try getting them from profiles
    if not search_terms:
        master_target_terms = set()
        for profile in config.profiles:
            if profile.target_terms:
                for term in profile.target_terms:
                    master_target_terms.add(term.lower())
        search_terms = list(master_target_terms)

    all_jobs = await scan_companies(tenant_ids, search_terms)
    
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
            title = str(job.get('title') or '').lower()
            loc = str(job.get('location') or '').lower()
            url = job.get('url') or ''
            company = job.get('company') or ''
            
            matches_title = True
            if profile.target_terms:
                from rapidfuzz import fuzz
                matches_title = any(fuzz.partial_ratio(term.lower(), title) > 75 or fuzz.token_set_ratio(term.lower(), title) > 75 for term in profile.target_terms)
                
            matches_loc = True
            if profile.target_locations:
                # NHS checks
                is_nhs = False
                url_lower = (job.get('url') or '').lower()
                company_lower = company.lower()
                if "jobs.nhs.uk" in url_lower or "nhs" in company_lower:
                    is_nhs = True
                
                broad_uk_terms = {"uk", "gb", "united kingdom"}
                user_searched_broad = any(l.lower() in broad_uk_terms for l in profile.target_locations)

                if is_nhs and user_searched_broad:
                    matches_loc = True
                else:
                    common_uk_locs = {"uk", "united kingdom", "gb", "england", "scotland", "wales", "northern ireland", "london", "manchester", "birmingham", "leeds", "glasgow", "liverpool", "newcastle", "sheffield", "belfast", "bristol", "edinburgh", "cardiff"}
                    
                    if user_searched_broad:
                        import re
                        matches_loc = any(re.search(r'\b' + re.escape(uk_term) + r'\b', loc) for uk_term in common_uk_locs)
                    else:
                        from rapidfuzz import fuzz
                        matches_loc = any(fuzz.partial_ratio(l.lower(), loc) > 75 or fuzz.token_set_ratio(l.lower(), loc) > 75 for l in profile.target_locations)
            
            if matches_title and matches_loc:
                is_spons, routes = is_sponsored(company, sponsors)
                if is_spons:
                    job['visa_routes'] = ', '.join(routes)
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
