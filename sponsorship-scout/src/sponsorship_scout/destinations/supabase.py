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
            fourteen_days_ago_string = (datetime.utcnow() - timedelta(days=14)).isoformat()
            
            def batch_delete_ids(ids_to_delete: List[str], label: str):
                if not ids_to_delete:
                    print(f"[Supabase] No {label} to delete.")
                    return
                del_batch_size = 200
                deleted_count = 0
                for j in range(0, len(ids_to_delete), del_batch_size):
                    chunk = ids_to_delete[j:j + del_batch_size]
                    supabase.table("jobs").delete().in_("id", chunk).execute()
                    deleted_count += len(chunk)
                print(f"[Supabase] Cleaned up {deleted_count} {label} in batches of {del_batch_size}.")

            # 1. Purge jobs unseen for > 14 days (applies to ALL jobs, including NHS)
            try:
                stale_ids = []
                while True:
                    resp = supabase.table("jobs").select("id").lt("last_seen_at", fourteen_days_ago_string).limit(1000).execute()
                    if not resp.data:
                        break
                    chunk_ids = [r["id"] for r in resp.data]
                    stale_ids.extend(chunk_ids)
                    batch_delete_ids(chunk_ids, "stale jobs (last_seen_at > 14 days)")
                    if len(chunk_ids) < 1000:
                        break
                if not stale_ids:
                    print("[Supabase] Cleaned up stale jobs (0 rows with last_seen_at > 14 days).")
            except Exception as e:
                print(f"[Supabase] Error purging stale jobs (last_seen_at > 14d): {e}")

            # 2. Purge Dead ATS Jobs (unseen > 3 days for non-NHS APIs)
            try:
                while True:
                    resp = supabase.table("jobs").select("id").lt("last_seen_at", three_days_ago_string).filter("url", "not.ilike", "%jobs.nhs.uk%").limit(1000).execute()
                    if not resp.data:
                        break
                    chunk_ids = [r["id"] for r in resp.data]
                    batch_delete_ids(chunk_ids, "dead ATS jobs (>3 days unseen)")
                    if len(chunk_ids) < 1000:
                        break
                print("[Supabase] Cleaned up dead ATS jobs (>3 days unseen).")
            except Exception as e:
                print(f"[Supabase] Error purging dead ATS jobs: {e}")

            # 3. Purge Ghost Jobs (created_at > 14 days ago)
            try:
                while True:
                    resp = supabase.table("jobs").select("id").lt("created_at", fourteen_days_ago_string).limit(1000).execute()
                    if not resp.data:
                        break
                    chunk_ids = [r["id"] for r in resp.data]
                    batch_delete_ids(chunk_ids, "ghost jobs (created_at > 14 days)")
                    if len(chunk_ids) < 1000:
                        break
                print("[Supabase] Cleaned up ghost jobs (>14 days old).")
            except Exception as e:
                print(f"[Supabase] Error purging ghost jobs: {e}")
                
        except Exception as e:
            print(f"[Supabase] Error upserting/deleting jobs: {e}")
