# In app/processing.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# --- CONSTANTS ---
BASE_PARAMS = {"wiki": "mobilelegends", "limit": 500}
TEAM_NORMALIZATION = { "AP.Bren": "Falcons AP.Bren", "ECHO": "Team Liquid PH" }

# --- API FETCHING & PROCESSING LOGIC ---
class LiquipediaAPI:
    def get_tournament_matches(self, tournament_path: str):
        try:
            api_key = os.getenv("LIQUIPEDIA_API_KEY")
            if not api_key:
                print("Error: LIQUIPEDIA_API_KEY not found.")
                return []
            
            headers = {"Authorization": f"Apikey {api_key}", "User-Agent": "MLBB-Analytics-Seeder/1.0"}
            params = BASE_PARAMS.copy()
            params['conditions'] = f"[[parent::{tournament_path}]]"
            url = "https://api.liquipedia.net/api/v3/match"
            
            resp = requests.get(url, headers=headers, params=params)
            resp.raise_for_status()
            
            raw_matches = resp.json().get("result", [])
            return self._enrich_matches(raw_matches)

        except Exception as e:
            print(f"API Error for path {tournament_path}: {e}")
            return []

    def _normalize_team(self, team_name: str) -> str:
        stripped_name = (team_name or "").strip()
        return TEAM_NORMALIZATION.get(stripped_name, stripped_name)

    def _get_stage_info(self, pagename: str, section: str) -> tuple[str, int]:
        source_string = section if '/' in section else pagename
        stage_type = source_string.split('/')[-1].replace('_', ' ').strip()
        stage_type_lower = stage_type.lower()
        
        priority = 99
        if "playoffs" in stage_type_lower or "finals" in stage_type_lower: priority = 40
        elif "rumble" in stage_type_lower or "play-in" in stage_type_lower: priority = 30
        elif "stage 2" in stage_type_lower: priority = 20
        elif "regular season" in stage_type_lower or "group" in stage_type_lower: priority = 10
            
        return stage_type if stage_type else "Uncategorized", priority

    def _enrich_matches(self, matches_raw: list) -> list:
        enriched_matches = []
        for m in matches_raw:
            if not isinstance(m, dict) or "match2opponents" not in m:
                continue

            # --- THIS IS THE CRITICAL FIX ---
            # Validate that both team names are present and are not placeholders.
            try:
                team1_name = m["match2opponents"][0].get("name")
                team2_name = m["match2opponents"][1].get("name")
                
                # If a name is missing, empty, or a known placeholder, skip the match.
                if not team1_name or not team2_name or team1_name.startswith('#?') or team2_name.startswith('#?'):
                    # print(f"Skipping match with invalid team name: {team1_name} vs {team2_name}")
                    continue
            except (IndexError, KeyError):
                # Skip if the match doesn't have two opponents
                continue
            # --- END OF FIX ---

            # Normalize team names
            m["match2opponents"][0]["name"] = self._normalize_team(team1_name)
            m["match2opponents"][1]["name"] = self._normalize_team(team2_name)

            # Add stage information
            stage_type, stage_priority = self._get_stage_info(m.get("pagename", ""), m.get("section", ""))
            m['stage_type'] = stage_type
            m['stage_priority'] = stage_priority
            
            enriched_matches.append(m)
        return enriched_matches

liquipedia_api = LiquipediaAPI()