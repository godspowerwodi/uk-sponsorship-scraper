import aiohttp
from typing import List, Tuple, Dict

async def fetch_lever(session: aiohttp.ClientSession, company: str) -> Tuple[str, List[Dict]]:
    try:
        async with session.get(f"https://api.lever.co/v0/postings/{company}", timeout=15, ssl=False) as resp:
            if resp.status == 200:
                data = await resp.json()
                return company, [{'title': j.get('text',''), 'location': j.get('categories',{}).get('location',''), 'url': j.get('hostedUrl','')} for j in data]
    except: pass
    return company, []
