import os
import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.crud import update_match
from app.processing import parse_and_enrich_matches
from app.models import Base
from app.database import engine

# --- Load Environment Variables ---
# Make sure you have your LIQUIPEDIA_API_KEY and DATABASE_URL in a .env file
load_dotenv()

# --- CONSTANTS (from original Streamlit project) ---

BASE_PARAMS = {"wiki": "mobilelegends", "limit": 500}

ALL_TOURNAMENTS = {
    'MPL ID Season 14': {'path': 'MPL/Indonesia/Season_14', 'region': 'Indonesia', 'year': 2024, 'live': False, 'league': 'MPL Indonesia', 'split': '2024 Split 2'},
    'MPL ID Season 16': {'path': 'MPL/Indonesia/Season_16', 'region': 'Indonesia', 'year': 2025, 'live': False, 'league': 'MPL Indonesia', 'split': '2025 Split 2'},
    'China Masters 2025': {'path': 'MLBB_China_Masters/2025', 'region': 'China', 'year': 2025, 'live': False, 'league': 'China Masters', 'split': '2025 Split 2'},
}

TEAM_NORMALIZATION = {
    "AP.Bren": "Falcons AP.Bren",
    "Falcons AP.Bren": "Falcons AP.Bren",
    "ECHO": "Team Liquid PH",
    "Team Liquid PH": "Team Liquid PH",
}

# --- DATA PROCESSING LOGIC (from original Streamlit project) ---

def normalize_team(n):
    return TEAM_NORMALIZATION.get((n or "").strip(), (n or "").strip())

def get_stage_info(pagename, section):
    source_string = section if '/' in section else pagename
    stage_type = source_string.split('/')[-1].replace('_', ' ').strip()
    stage_type_lower = stage_type.lower()
    
    if "playoffs" in stage_type_lower or "finals" in stage_type_lower or "knockout" in stage_type_lower:
        stage_priority = 40
    elif "rumble" in stage_type_lower or "play-in" in stage_type_lower:
        stage_priority = 30
    elif "stage 2" in stage_type_lower:
        stage_priority = 20
    elif "regular season" in stage_type_lower or "group" in stage_type_lower or "swiss" in stage_type_lower or "week" in stage_type_lower or "stage 1" in stage_type_lower:
        stage_priority = 10
    else:
        stage_priority = 99
        
    return stage_type if stage_type else "Uncategorized", stage_priority

def parse_and_enrich_matches(matches_raw, tournament_name):
    enriched_matches = []
    for m in matches_raw:
        if not isinstance(m, dict):
            continue
        
        # Add the tournament name to the match data
        m['tournament'] = tournament_name
        
        if "match2opponents" in m:
            for opp in m["match2opponents"]:
                opp["name"] = normalize_team(opp.get("name"))

        stage_type, stage_priority = get_stage_info(m.get("pagename", ""), m.get("section", ""))
        m['stage_type'] = stage_type
        m['stage_priority'] = stage_priority
        
        enriched_matches.append(m)
    return enriched_matches

# --- API FETCHING LOGIC (from original Streamlit project) ---

def fetch_from_api(tournament_path):
    try:
        api_key = os.getenv("LIQUIPEDIA_API_KEY")
        if not api_key:
            print("Error: LIQUIPEDIA_API_KEY not found in .env file.")
            return {'error': 'API key not configured.'}
        
        headers = {"Authorization": f"Apikey {api_key}", "User-Agent": "MLBB-Analytics-Seeder/1.0"}
        params = BASE_PARAMS.copy()
        params['conditions'] = f"[[parent::{tournament_path}]]"
        url = "https://api.liquipedia.net/api/v3/match"
        
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json().get("result", [])
        
    except Exception as e:
        print(f"API Error for path {tournament_path}: {e}")
        return {'error': str(e)}

# --- MAIN SEEDING SCRIPT ---

def seed_database():
    db: Session = SessionLocal()
    
    # We will only seed historical (not live) tournaments
    historical_tournaments = {name: data for name, data in ALL_TOURNAMENTS.items() if not data['live']}

    for name, data in historical_tournaments.items():
        print(f"\nFetching data for: {name}...")
        
        raw_matches = fetch_from_api(data['path'])
        
        if 'error' in raw_matches:
            print(f"Skipping {name} due to API fetch error.")
            continue
            
        if not raw_matches:
            print(f"No matches found for {name}.")
            continue
            
        print(f"Found {len(raw_matches)} matches. Processing and saving to database...")
        
        enriched_matches = parse_and_enrich_matches(raw_matches, name)
        
        for i, match_data in enumerate(enriched_matches):
            try:
                # The crud function handles the entire transaction
                update_match(db=db, match_data=match_data)
                print(f"  ({i+1}/{len(enriched_matches)}) Saved match with Liquipedia ID: {match_data['pageid']}")
            except Exception as e:
                print(f"  - Failed to save match {match_data.get('pageid', 'N/A')}: {e}")

    db.close()
    print("\nDatabase seeding process completed!")

if __name__ == "__main__":
    seed_database()