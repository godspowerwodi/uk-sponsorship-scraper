import os
from supabase import create_client
import concurrent.futures
import time

url = os.environ.get("SUPABASE_URL", "http://localhost:8000")
key = os.environ.get("SUPABASE_KEY", "dummy")

def test():
    supabase = create_client(url, key)
    
    def fetch_chunk(chunk):
        print(f"Fetching chunk {chunk}")
        time.sleep(0.1)
        return [{"id": chunk, "description": "hello"}]
        
    chunks = [1, 2, 3, 4, 5]
    res_map = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_chunk, c) for c in chunks]
        for future in concurrent.futures.as_completed(futures):
            for row in future.result():
                res_map[row["id"]] = row["description"]
    
    print(res_map)

if __name__ == "__main__":
    test()

