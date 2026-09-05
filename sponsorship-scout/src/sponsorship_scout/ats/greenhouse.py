import aiohttp
from typing import List, Tuple, Dict

async def fetch_greenhouse(session: aiohttp.ClientSession, company: str) -> Tuple[str, List[Dict]]:
    try:
        async with session.get(f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs", timeout=15, ssl=False) as resp:
            if resp.status == 200:
                data = await resp.json()
                return company, [{'title': j.get('title',''), 'location': j.get('location',{}).get('name',''), 'url': j.get('absolute_url','')} for j in data.get('jobs', [])]
    except: pass
    return company, []
