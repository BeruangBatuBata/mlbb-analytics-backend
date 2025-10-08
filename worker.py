# In worker.py
import os
import requests
from celery import Celery
from dotenv import load_dotenv

from app.database import SessionLocal
from app import crud

# Load environment variables from .env file
load_dotenv()

# --- Celery Configuration ---
REDIS_URL = os.getenv("REDIS_URL")
LIQUIPEDIA_API_KEY = os.getenv("LIQUIPEDIA_API_KEY") # Make sure to add this to your .env file

if not REDIS_URL:
    raise ValueError("No REDIS_URL environment variable set")
if not LIQUIPEDIA_API_KEY:
    raise ValueError("No LIQUIPEDIA_API_KEY environment variable set. Please get one from Liquipedia.")

celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)


# --- API Fetching Function (adapted from your original project) ---
def fetch_match_data(page_title: str):
    """Fetches a single match record from the Liquipedia API."""
    headers = {
        "Authorization": f"Apikey {LIQUIPEDIA_API_KEY}",
        "User-Agent": "MLBB-Analytics-Backend/1.0 (your-email@example.com)"
    }
    params = {
        "wiki": "mobilelegends",
        "conditions": f"[[pagename::{page_title}]]"
    }
    url = "https://api.liquipedia.net/api/v3/match"
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        results = response.json().get("result", [])
        if results:
            return results # Return the first match found
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Liquipedia API: {e}")
        return None

# --- Celery Task Definition ---
@celery_app.task
def process_match_update(page_title: str):
    """
    Background task to fetch match data and save it to the database.
    This version is fully robust and validates for the correct 'pageid' key.
    """
    print(f"--- Task Received: Processing update for '{page_title}' ---")
    
    list_of_matches = fetch_match_data(page_title)
    
    if list_of_matches:
        db = SessionLocal()
        try:
            for match_data in list_of_matches:
                # --- FINAL FIX: Check for dict type AND the presence of 'pageid' ---
                if isinstance(match_data, dict) and 'pageid' in match_data:
                    print(f"Processing match Page ID: {match_data.get('pageid')}")
                    crud.update_match(db, match_data)
                else:
                    print(f"Skipping invalid or incomplete item in API response: {match_data}")
                # -------------------------------------------------------------------
        finally:
            db.close()
    else:
        print(f"Could not fetch data for '{page_title}' or no matches were found.")
        
    print(f"--- Task Finished: Completed processing for '{page_title}' ---")
    return f"Completed processing for {page_title}"