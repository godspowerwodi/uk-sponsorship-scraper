import aiohttp
from typing import List, Tuple, Dict

import asyncio
from bs4 import BeautifulSoup

async def fetch_ashby(session: aiohttp.ClientSession, company: str) -> Tuple[str, List[Dict]]:
    try:
        async with session.get(f"https://api.ashbyhq.com/posting-api/job-board/{company}", timeout=15, ssl=False) as resp:
            if resp.status == 200:
                data = await resp.json()
                jobs = [{'title': j.get('title') or '', 'location': j.get('location') or '', 'url': j.get('jobUrl') or '', 'salary': '', 'description': j.get('descriptionPlain') or j.get('descriptionHtml') or ''} for j in data.get('jobs', [])]
                
                async def fetch_desc(job):
                    if job.get('description'):
                        job['description'] = BeautifulSoup(job['description'], 'html.parser').get_text(separator=' ', strip=True)
                        return
                    if job['url']:
                        try:
                            async with session.get(job['url'], timeout=10, ssl=False) as r:
                                if r.status == 200:
                                    html = await r.text()
                                    job['description'] = BeautifulSoup(html, 'html.parser').get_text(separator=' ', strip=True)
                        except: pass
                        
                await asyncio.gather(*(fetch_desc(job) for job in jobs))
                return company, jobs
    except: pass
    return company, []
