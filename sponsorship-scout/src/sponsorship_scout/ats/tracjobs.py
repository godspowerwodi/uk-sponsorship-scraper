import asyncio
import aiohttp
from typing import List, Tuple, Dict
import urllib.parse
from bs4 import BeautifulSoup

def _parse_tracjobs_html(text: str) -> List[Dict]:
    jobs = []
    soup = BeautifulSoup(text, 'html.parser')
    job_blocks = soup.find_all('li', attrs={'data-test': 'search-result'})
    
    for block in job_blocks:
        title_elem = block.find('a', attrs={'data-test': 'search-result-job-title'})
        loc_block = block.find('div', attrs={'data-test': 'search-result-location'})
        salary_elem = block.find('li', attrs={'data-test': 'search-result-salary'})
        
        if title_elem and loc_block:
            title = title_elem.get_text(strip=True)
            link = title_elem.get('href', '')
            
            h3_elem = loc_block.find('h3')
            company = ''
            location = ''
            if h3_elem:
                company = "".join(h3_elem.find_all(string=True, recursive=False)).strip()
                loc_elem = h3_elem.find('div', class_='location-font-size')
                if loc_elem:
                    location = loc_elem.get_text(strip=True)
            
            salary = ''
            if salary_elem:
                strong = salary_elem.find('strong')
                if strong:
                    salary = strong.get_text(strip=True)
            
            jobs.append({
                'title': title,
                'company': company or "NHS",
                'location': location or 'UK',
                'salary': salary,
                'url': f"https://www.jobs.nhs.uk{link}" if link.startswith('/') else link
            })
            
    return jobs

async def fetch_tracjobs(session: aiohttp.ClientSession, search_terms: List[str]) -> Tuple[str, List[Dict]]:
    if not search_terms:
        return "TracJobs", []
        
    jobs = []
    
    async def fetch_page(term: str, page: int):
        encoded_term = urllib.parse.quote(term)
        url = f"https://www.jobs.nhs.uk/candidate/search/results?keyword={encoded_term}&page={page}"
        try:
            async with session.get(url, timeout=15, ssl=False) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return _parse_tracjobs_html(text)
        except Exception:
            pass
        return []

    for term in search_terms:
        tasks = [fetch_page(term, page) for page in range(1, 21)]
        results = await asyncio.gather(*tasks)
        
        for parsed in results:
            if parsed:
                jobs.extend(parsed)
                
        if len(jobs) >= 200:
            break
            
    return "TracJobs", jobs[:200]
