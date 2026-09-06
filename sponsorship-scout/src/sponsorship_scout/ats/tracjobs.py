import aiohttp
from typing import List, Tuple, Dict
import urllib.parse
from bs4 import BeautifulSoup

async def fetch_tracjobs(session: aiohttp.ClientSession, search_terms: List[str]) -> Tuple[str, List[Dict]]:
    if not search_terms:
        return "TracJobs", []
        
    jobs = []
    for term in search_terms:
        encoded_term = urllib.parse.quote(term)
        url = f"https://apps.trac.jobs/search/?keywords={encoded_term}"
        try:
            async with session.get(url, timeout=15, ssl=False) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    soup = BeautifulSoup(text, 'html.parser')
                    job_blocks = soup.find_all('div', class_='job-result')
                    if not job_blocks:
                        job_blocks = soup.find_all('div', class_='job')
                    
                    for block in job_blocks:
                        title_elem = block.find('a', href=True)
                        employer_elem = block.find(class_=lambda c: c and 'employer' in c.lower())
                        loc_elem = block.find(class_=lambda c: c and 'location' in c.lower())
                        
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            link = title_elem['href']
                            company = employer_elem.get_text(strip=True) if employer_elem else "NHS Trust"
                            location = loc_elem.get_text(strip=True) if loc_elem else 'UK'
                            
                            jobs.append({
                                'title': title,
                                'company': company,
                                'location': location,
                                'url': f"https://apps.trac.jobs{link}" if link.startswith('/') else link
                            })
                            
                        if len(jobs) >= 200:
                            break
        except Exception:
            pass
            
        if len(jobs) >= 200:
            break
            
    return "TracJobs", jobs[:200]
