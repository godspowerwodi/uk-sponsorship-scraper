import requests
from typing import List, Dict

def send_to_discord(jobs: List[Dict], webhook_url: str):
    if not webhook_url:
        return

    for job in jobs:
        embed = {
            "title": f"?? New Sponsored Role: {job['company']} - {job['title']}",
            "description": f"**Location:** {job['location']}\n**Company:** {job['company'].title()}\n\n[Apply Here]({job['url']})",
            "color": 5814783,
            "footer": {"text": "Sponsorship Scout"}
        }
        
        data = {
            "content": "", 
            "embeds": [embed]
        }
        
        try:
            resp = requests.post(webhook_url, json=data, verify=False)
            print(f"Discord response [{job['company']}]: HTTP {resp.status_code}")
        except Exception as e:
            print(f"Error sending to Discord: {e}")
