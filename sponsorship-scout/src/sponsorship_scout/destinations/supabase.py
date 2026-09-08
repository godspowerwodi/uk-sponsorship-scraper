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
            "created_at": job.get('added_date')
        }
        records.append(record)
        
    if records:
        try:
            response = supabase.table("jobs").upsert(records).execute()
            print(f"[Supabase] Successfully upserted {len(records)} jobs to Supabase.")
            
            seven_days_ago_string = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            delete_response = supabase.table("jobs").delete().lt("created_at", seven_days_ago_string).execute()
            print(f"[Supabase] Cleaned up stale jobs older than {seven_days_ago_string}.")
        except Exception as e:
            print(f"[Supabase] Error upserting/deleting jobs: {e}")
