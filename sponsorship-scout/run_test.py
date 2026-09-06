import asyncio
import aiohttp
from sponsorship_scout.ats.tracjobs import fetch_tracjobs

async def main():
    async with aiohttp.ClientSession() as session:
        name, jobs = await fetch_tracjobs(session, ["nurse"])
        print(f"Scraper: {name}")
        print(f"Found {len(jobs)} jobs")
        if jobs:
            print(f"First job: {jobs[0]}")

if __name__ == "__main__":
    asyncio.run(main())
