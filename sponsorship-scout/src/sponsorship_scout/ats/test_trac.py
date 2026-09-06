import asyncio
import aiohttp
from tracjobs import fetch_tracjobs

async def main():
    async with aiohttp.ClientSession() as s:
        res = await fetch_tracjobs(s, ['nurse'])
        print(len(res[1]))
        if res[1]:
            print(res[1][:2])
        else:
            print("No jobs found.")

if __name__ == "__main__":
    asyncio.run(main())
