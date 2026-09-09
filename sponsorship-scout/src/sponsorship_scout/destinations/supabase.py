import os
from typing import List, Dict
from supabase import create_client, Client
import hashlib
from datetime import datetime, timedelta

def get_job_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()

def send_to_supabase(jobs: List[Dict]):
    if not jobs:
        return
        
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("[Supabase] Warning: SUPABASE_URL or SUPABASE_KEY not found in environment.")
        return
        
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"[Supabase] Error initializing client: {e}")
        return
        
    records = []
    for job in jobs:
        url = job.get('url') or ''
        job_id = get_job_id(url) if url else None
        
        if not job_id:
            continue
            
        record = {
            "id": job_id,
            "title": job.get('title'),
            "company": job.get('company'),
            "location": job.get('location'),
            "url": url,
            "description": job.get('description'),
            "salary": job.get('salary'),
            "visa_routes": job.get('visa_routes') or "Unknown",
            "last_seen_at": datetime.utcnow().isoformat()
        }
        records.append(record)
        
    if records:
        try:
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                supabase.table("jobs").upsert(batch).execute()
            print(f"[Supabase] Successfully upserted {len(records)} jobs to Supabase in batches of {batch_size}.")
            
            three_days_ago_string = (datetime.utcnow() - timedelta(days=3)).isoformat()
            thirty_days_ago_string = (datetime.utcnow() - timedelta(days=30)).isoformat()
            
            # 1. Purge Dead Jobs (removed from API)
            supabase.table("jobs").delete().lt("last_seen_at", three_days_ago_string).execute()
            
            # 2. Purge Ghost Jobs (stale on API)
            supabase.table("jobs").delete().lt("created_at", thirty_days_ago_string).execute()
            
            print(f"[Supabase] Cleaned up dead jobs (>3 days unseen) and ghost jobs (>30 days old).")
        except Exception as e:
            print(f"[Supabase] Error upserting/deleting jobs: {e}")
