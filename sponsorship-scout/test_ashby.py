import asyncio
import aiohttp
from sponsorship_scout.ats.ashby import fetch_ashby

async def main():
    async with aiohttp.ClientSession() as s:
        res = await fetch_ashby(s, 'neudata')
        print(res)

asyncio.run(main())
