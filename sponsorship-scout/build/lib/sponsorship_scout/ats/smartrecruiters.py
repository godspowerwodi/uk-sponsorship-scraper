import aiohttp
from typing import List, Tuple, Dict

async def fetch_smartrecruiters(session: aiohttp.ClientSession, company: str) -> Tuple[str, List[Dict]]:
    try:
        async with session.get(f"https://api.smartrecruiters.com/v1/companies/{company}/postings", timeout=15, ssl=False) as resp:
            if resp.status == 200:
                data = await resp.json()
                jobs = []
                for j in data.get('content', []):
                    loc_name = j.get('location', {}).get('city') or ''
                    url = f"https://jobs.smartrecruiters.com/{company}/{j.get('id') or ''}"
                    jobs.append({'title': j.get('name') or '', 'location': loc_name, 'url': url})
                return company, jobs
    except: pass
    return company, []
