import asyncio
import aiohttp
from sponsorship_scout.ats.tracjobs import fetch_tracjobs

async def main():
    async with aiohttp.ClientSession() as session:
        name, jobs = await fetch_tracjobs(session, [])
        print(f"Got {len(jobs)} jobs")

if __name__ == "__main__":
    asyncio.run(main())
