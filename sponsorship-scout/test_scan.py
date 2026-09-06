import asyncio
from sponsorship_scout.core.engine import scan_companies

async def main():
    jobs = await scan_companies({'neudata'})
    print(jobs)

asyncio.run(main())
