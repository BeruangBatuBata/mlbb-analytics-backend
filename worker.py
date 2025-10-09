import os
import requests
from celery import Celery
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.crud import update_match
from app.processing import parse_and_enrich_matches

load_dotenv()

# --- Celery Configuration ---
celery_app = Celery(
    "worker",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")
)
celery_app.conf.update(
    task_track_started=True,
)

def fetch_all_tournament_matches(tournament_path: str):
    """
    Fetches ALL matches for a given top-level tournament path.
    """
    try:
        api_key = os.getenv("LIQUIPEDIA_API_KEY")
        if not api_key:
            print("Error: LIQUIPEDIA_API_KEY not found.")
            return {'error': 'API key not configured.'}

        headers = {"Authorization": f"Apikey {api_key}", "User-Agent": "MLBB-Analytics-Worker/1.0"}
        params = {"wiki": "mobilelegends", "limit": 500}
        # This is the key: we query the top-level tournament path
        params['conditions'] = f"[[parent::{tournament_path}]]"
        url = "https://api.liquipedia.net/api/v3/match"

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        
        return resp.json().get("result", [])

    except Exception as e:
        print(f"API Error fetching matches for tournament '{tournament_path}': {e}")
        return {'error': str(e)}

# --- Celery Task Definition ---
@celery_app.task
def process_liquipedia_update(page_title: str, tournament_name: str):
    """
    Celery task that receives a webhook notification for ANY tournament sub-page,
    determines the top-level tournament, and refreshes ALL its matches.
    """
    print(f"Received update notification for page: {page_title}")

    # --- THIS IS THE CRITICAL FIX ---
    # Determine the top-level tournament path from the incoming page_title.
    # This logic mirrors how we derive the tournament_name in main.py.
    parts = page_title.split('/')
    if parts[0] == "MPL":
        top_level_path = f"{parts[0]}/{parts[1]}/{parts[2]}"
    elif parts[0] == "MSC":
        top_level_path = f"{parts[0]}/{parts[1]}"
    else:
        top_level_path = parts[0] # Fallback for other structures
    # --------------------------------

    print(f"Identified top-level tournament path: {top_level_path}. Refreshing all matches.")
    
    # Step 1: Fetch all matches for the entire tournament
    all_matches = fetch_all_tournament_matches(top_level_path)

    if not all_matches or 'error' in all_matches:
        print(f"Failed to fetch any matches for tournament '{top_level_path}'. Aborting task.")
        return

    print(f"Found {len(all_matches)} total matches for {tournament_name}. Processing...")

    # Step 2: Enrich all matches
    enriched_matches = parse_and_enrich_matches(all_matches, tournament_name)
    
    # Step 3: Save every match. The CRUD function handles create/update logic.
    db: Session = SessionLocal()
    try:
        for i, match_data in enumerate(enriched_matches):
            try:
                # This will create new matches or update existing ones
                update_match(db=db, match_data=match_data)
            except Exception as e:
                print(f"    - DB error for match {match_data.get('pageid', 'N/A')}: {e}")
        print(f"Successfully refreshed database for tournament: {tournament_name}.")
    finally:
        db.close()