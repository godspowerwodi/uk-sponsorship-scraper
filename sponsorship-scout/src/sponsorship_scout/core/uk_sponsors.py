import csv
import aiohttp
import asyncio
import io
import requests
import urllib3
import re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup
from typing import Set, Tuple, List

def fetch_sponsors_and_generate_tenants(industry_keywords: Set[str]) -> Tuple[Set[str], Set[str]]:
    print(f"Fetching the latest UK Register of Licensed Sponsors CSV and filtering by {len(industry_keywords)} industry keywords...")
    
    # Try direct URL first, fallback to scraping gov.uk if 404
    csv_url = "https://assets.publishing.service.gov.uk/media/6a8ff32b5a0c25165ae465cc/SP_-_Worker_and_Temporary_Worker_Web_Register_-_2026-08-27.csv"
    
    try:
        resp = requests.get(csv_url, timeout=15, verify=False)
        if resp.status_code != 200:
            page = requests.get("https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers", timeout=10, verify=False)
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
                
                if any(kw in raw_name for kw in industry_keywords):
                    clean_name = raw_name.replace(" ltd", "").replace(" limited", "").replace(" uk", "")
                    clean_name = re.sub(r'[^a-z0-9]', '', clean_name)
                    if len(clean_name) > 3:
                        tenant_ids.add(clean_name)
                        
        print(f"Loaded {len(sponsors)} licensed sponsors.")
        print(f"Generated {len(tenant_ids)} potential ATS tenant IDs from target industries.")
        return sponsors, tenant_ids
        
    except Exception as e:
        print(f"Error fetching sponsors: {e}")
        return set(), set()

def is_sponsored(company_name: str, sponsors_set: Set[str]) -> bool:
    company_norm = company_name.strip().lower()
    if company_norm in sponsors_set:
        return True
    for s in sponsors_set:
        if company_norm in s or s in company_norm:
            if len(company_norm) > 4 and len(s) > 4:
                return True
    return False
