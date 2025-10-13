# In seed_db.py

import json
from tqdm import tqdm
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models, crud
from app.processing import liquipedia_api

def seed_database():
    """
    Reads tournaments from tournaments.json, fetches their data from the
    Liquipedia API, and populates the database.
    """
    db: Session = SessionLocal()
    # This creates tables if they don't exist
    models.Base.metadata.create_all(bind=engine)

    try:
        with open("tournaments.json", "r") as f:
            tournaments_to_seed = json.load(f)
    except FileNotFoundError:
        print("ERROR: tournaments.json not found. Please create it.")
        db.close()
        return

    print(f"Found {len(tournaments_to_seed)} tournaments to process from config file.")

    for tournament_config in tqdm(tournaments_to_seed, desc="Processing Tournaments"):
        liquipedia_name = tournament_config.get("liquipedia_name")
        display_name = tournament_config.get("display_name")
        region = tournament_config.get("region")
        split = tournament_config.get("split")

        if not all([liquipedia_name, display_name, region, split]):
            print(f"\nWARNING: Skipping invalid tournament entry: {tournament_config}")
            continue

        try:
            # The API handler now returns clean, enriched data
            enriched_matches = liquipedia_api.get_tournament_matches(liquipedia_name)
            
            if not enriched_matches:
                print(f"\nNo match data found or an API error occurred for {display_name}.")
                continue

            for match_data in tqdm(enriched_matches, desc=f"Seeding {display_name}", leave=False):
                # Add the display name for the tournament to the match data
                match_data["tournament"] = display_name
                
                # Call the CRUD function to save to the database
                crud.update_tournament_and_match(db, match_data, region, split)

        except Exception as e:
            print(f"\nAn unexpected error occurred while processing {display_name}: {e}")

    print("Database seeding complete.")
    db.close()

if __name__ == "__main__":
    seed_database()