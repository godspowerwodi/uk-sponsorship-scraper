import aiohttp
from typing import List, Tuple, Dict
import urllib.parse
import re

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
                    # Trac jobs often has jobs in a list. We'll try a generic parsing.
                    # For a real implementation, BeautifulSoup is better, but regex avoids missing dependencies.
                    # Look for job links: <a href="/job/...">Title</a>
                    # and employers: <span class="employer">Employer Name</span>
                    
                    # We'll do a very basic regex that just grabs blocks that might represent jobs
                    job_blocks = text.split('job-result')
                    for block in job_blocks[1:]:
                        title_match = re.search(r'<a[^>]+href="(/job/[^"]+)"[^>]*>([^<]+)</a>', block)
                        employer_match = re.search(r'employer"[^>]*>([^<]+)<', block, re.IGNORECASE)
                        
                        if title_match:
                            link = title_match.group(1)
                            title = title_match.group(2).strip()
                            company = employer_match.group(1).strip() if employer_match else "NHS Trust"
                            
                            jobs.append({
                                'title': title,
                                'company': company,
                                'location': 'UK', # Could parse location similarly
                                'url': f"https://apps.trac.jobs{link}"
                            })
                            
                        if len(jobs) >= 200:
                            break
        except Exception:
            pass
            
        if len(jobs) >= 200:
            break
            
    return "TracJobs", jobs[:200]
