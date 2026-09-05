import aiohttp
from typing import List, Tuple, Dict

async def fetch_ashby(session: aiohttp.ClientSession, company: str) -> Tuple[str, List[Dict]]:
    try:
        async with session.get(f"https://api.ashbyhq.com/posting-api/job-board/{company}", timeout=15, ssl=False) as resp:
            if resp.status == 200:
                data = await resp.json()
                return company, [{'title': j.get('title') or '', 'location': j.get('location') or '', 'url': j.get('jobUrl') or ''} for j in data.get('jobs', [])]
    except: pass
    return company, []
