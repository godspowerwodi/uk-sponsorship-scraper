import json
import requests
from typing import List, Dict

def send_to_gist(jobs: List[Dict], gist_id: str, token: str, filename: str):
    if not gist_id or not token:
        return
        
    # First, fetch existing gist
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        url = f"https://api.github.com/gists/{gist_id}"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            gist_data = resp.json()
            existing_content = "[]"
            if filename in gist_data.get("files", {}):
                existing_content = gist_data["files"][filename]["content"]
            
            queue = json.loads(existing_content) if existing_content else []
            existing_urls = {j['url'] for j in queue}
            
            new_added = False
            for job in jobs:
                if job['url'] not in existing_urls:
                    queue.append(job)
                    new_added = True
                    
            if new_added:
                update_data = {
                    "files": {
                        filename: {
                            "content": json.dumps(queue, indent=4)
                        }
                    }
                }
                patch_resp = requests.patch(url, headers=headers, json=update_data)
                print(f"Gist update response: HTTP {patch_resp.status_code}")
    except Exception as e:
        print(f"Error updating Gist: {e}")
