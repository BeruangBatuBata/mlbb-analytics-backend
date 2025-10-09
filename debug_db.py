# In debug_db.py
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.database import SessionLocal
from app.models import Match, MatchHero, Tournament

def get_database_counts(db: Session):
    """
    Connects to the database and gets the total count of matches and games.
    """
    print("\n" + "="*60)
    print("DEBUG: Querying database for total counts...")

    # 1. Count total number of matches (series)
    total_matches = db.query(func.count(Match.id)).scalar()

    # 2. Count total number of unique games
    distinct_games_query = select(MatchHero.match_id, MatchHero.game_number).distinct()
    total_games = db.execute(select(func.count()).select_from(distinct_games_query.subquery())).scalar_one_or_none() or 0
    
    # 3. Count total number of tournaments
    total_tournaments = db.query(func.count(Tournament.id)).scalar()


    print("\n--- Database Ground Truth ---")
    print(f"Total Tournaments Stored: {total_tournaments}")
    print(f"Total Matches (Series) Stored: {total_matches}")
    print(f"Total Unique Games Stored: {total_games}")
    print("="*60 + "\n")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        get_database_counts(db)
    finally:
        db.close()