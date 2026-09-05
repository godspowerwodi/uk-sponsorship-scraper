import aiohttp
from typing import List, Tuple, Dict

async def fetch_ashby(session: aiohttp.ClientSession, company: str) -> Tuple[str, List[Dict]]:
    try:
        async with session.get(f"https://api.ashbyhq.com/posting-api/job-board/{company}", timeout=15, ssl=False) as resp:
            if resp.status == 200:
                data = await resp.json()
                return company, [{'title': j.get('title',''), 'location': j.get('location',''), 'url': j.get('url','')} for j in data.get('jobs', [])]
    except: pass
    return company, []
