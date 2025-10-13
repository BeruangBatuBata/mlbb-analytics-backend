# In worker.py

from celery import Celery
from app.database import SessionLocal
from app.processing import liquipedia_api
from app import crud, models

# Configure Celery
# Make sure your REDIS_URL is set in your .env file
celery_app = Celery("worker", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")

@celery_app.task
def process_liquipedia_update(page: str, tournament_name: str):
    """
    Celery task to handle a webhook update from Liquipedia.
    """
    print(f"Processing update for: {tournament_name}")
    db = SessionLocal()
    try:
        # 1. Find the tournament in our database to get its region and split.
        tournament = db.query(models.Tournament).filter_by(name=tournament_name).first()
        
        if not tournament:
            print(f"Warning: Received webhook for an unknown tournament: {tournament_name}. Skipping.")
            return

        # 2. Fetch the latest match data from the API.
        enriched_matches = liquipedia_api.get_tournament_matches(page)

        if not enriched_matches:
            print(f"No match data found for updated page: {page}")
            return

        # 3. Process each match using the correct function and the data from our database.
        for match_data in enriched_matches:
            match_data["tournament"] = tournament.name # Ensure display name is consistent
            
            # Use the correct, renamed function
            crud.update_tournament_and_match(
                db, 
                match_data, 
                region=tournament.region, 
                split=tournament.split
            )
        
        print(f"Successfully processed update for: {tournament_name}")
        
    except Exception as e:
        print(f"An error occurred during webhook processing for {tournament_name}: {e}")
    finally:
        db.close()