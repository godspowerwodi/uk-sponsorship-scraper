import aiohttp
from typing import List, Tuple, Dict
from bs4 import BeautifulSoup

async def fetch_greenhouse(session: aiohttp.ClientSession, company: str) -> Tuple[str, List[Dict]]:
    try:
        async with session.get(f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true", timeout=15, ssl=False) as resp:
            if resp.status == 200:
                data = await resp.json()
                jobs = []
                for j in data.get('jobs', []):
                    desc = BeautifulSoup(j.get('content', ''), 'html.parser').get_text(separator=' ', strip=True)
                    jobs.append({
                        'title': j.get('title') or '',
                        'location': j.get('location',{}).get('name') or '',
                        'url': j.get('absolute_url') or '',
                        'salary': '',
                        'description': desc
                    })
                return company, jobs
    except: pass
    return company, []
