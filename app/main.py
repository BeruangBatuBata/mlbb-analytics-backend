# In app/main.py

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, case

# Import the get_db function to provide database sessions to endpoints
from .database import engine, get_db
from . import models, schemas
from worker import celery_app

# This line ensures that all tables are created in the database when the app starts
models.Base.metadata.create_all(bind=engine)

# Initialize the main FastAPI application
app = FastAPI(
    title="MLBB Pro-Scene Analytics API",
    description="An API to serve data for the MLBB Analytics Dashboard.",
    version="0.1.0",
)

# --- CORS MIDDLEWARE ---
# This block is essential for allowing your frontend (on localhost:3000)
# to make requests to your backend (on localhost:8000).
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)

# --- API Endpoints ---

@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the MLBB Analytics API!"}


@app.post("/webhooks/liquipedia")
async def receive_liquipedia_webhook(payload: schemas.LiquipediaWebhookPayload):
    """Receives webhook notifications from Liquipedia and dispatches them to the background worker."""
    page_name = payload.page
    print(f"Webhook received for page '{page_name}'. Handing off to worker.")
    
    # Send the task to the Celery worker for background processing
    celery_app.send_task('worker.process_match_update', args=[page_name])
    
    return {"status": "success", "message": "Webhook received and task dispatched"}


@app.get("/api/stats")
def get_hero_statistics(db: Session = Depends(get_db)):
    """
    Calculates and returns REAL hero statistics from the database.
    This version contains the corrected SQLAlchemy query syntax.
    """
    # Get the total number of unique matches that have pick/ban data.
    total_matches_with_data = db.query(func.count(func.distinct(models.MatchHero.match_id))).scalar() or 0
    
    if total_matches_with_data == 0:
        print("No matches with hero data found in DB, returning empty list.")
        return []

    print(f"Calculating stats based on {total_matches_with_data} matches with pick/ban data...")

    # This query joins Heroes, MatchHeroes, and Matches to calculate all stats.
    hero_stats = db.query(
        models.Hero.name,
        # --- CORRECTED SYNTAX: Pass the tuple directly to case() ---
        func.sum(case((models.MatchHero.type == 'pick', 1), else_=0)).label('picks'),
        func.sum(case((models.MatchHero.type == 'ban', 1), else_=0)).label('bans'),
        func.sum(case(
            (
                (
                    (models.MatchHero.type == 'pick') & 
                    (
                        ((models.Match.winner_id == models.Match.team1_id) & (models.MatchHero.team_id == models.Match.team1_id)) |
                        ((models.Match.winner_id == models.Match.team2_id) & (models.MatchHero.team_id == models.Match.team2_id))
                    )
                ),
                1
            ),
            else_=0
        )).label('wins')
        # -----------------------------------------------------------
    ).select_from(models.Hero)\
     .join(models.MatchHero, models.Hero.id == models.MatchHero.hero_id)\
     .join(models.Match, models.MatchHero.match_id == models.Match.id)\
     .group_by(models.Hero.name)\
     .all()

    results = []
    for row in hero_stats:
        hero_name, picks, bans, wins = row
        
        picks = int(picks) if picks is not None else 0
        bans = int(bans) if bans is not None else 0
        wins = int(wins) if wins is not None else 0

        pick_rate = (picks / total_matches_with_data) * 100 if total_matches_with_data > 0 else 0
        ban_rate = (bans / total_matches_with_data) * 100 if total_matches_with_data > 0 else 0
        win_rate = (wins / picks) * 100 if picks > 0 else 0
        presence = ((picks + bans) / total_matches_with_data) * 100 if total_matches_with_data > 0 else 0

        results.append({
            "Hero": hero_name,
            "Picks": picks,
            "Bans": bans,
            "Pick Rate (%)": round(pick_rate, 2),
            "Ban Rate (%)": round(ban_rate, 2),
            "Win Rate (%)": round(win_rate, 2),
            "Presence (%)": round(presence, 2),
        })

    # Sort results by presence for better presentation
    results.sort(key=lambda x: x['Presence (%)'], reverse=True)

    print(f"Successfully calculated and returning stats for {len(results)} heroes.")
    return results