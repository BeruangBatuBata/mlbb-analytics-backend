# In app/main.py
from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, crud, schemas
from .database import engine, get_db
from worker import process_liquipedia_update
from typing import List, Optional

# This line ensures that the database tables are created based on your models
# the first time the application starts.
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- CORS Middleware ---
# This allows your frontend (running on a different address) to make requests
# to this backend. The "*" allows all origins, which is fine for development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.get("/api/tournaments", response_model=list[schemas.Tournament])
def get_tournaments_endpoint(db: Session = Depends(get_db)):
    """
    API endpoint to get a list of all available tournaments for filtering.
    """
    return crud.get_all_tournaments(db)

@app.get("/api/teams", response_model=list[schemas.Team])
def get_teams_endpoint(
    db: Session = Depends(get_db),
    tournaments: Optional[List[str]] = Query(None) # Add optional filter
):
    return crud.get_all_teams(db, tournament_names=tournaments)

@app.get("/api/stages", response_model=list[str])
def get_stages_endpoint(
    db: Session = Depends(get_db),
    tournaments: Optional[List[str]] = Query(None) # Add optional filter
):
    return crud.get_all_stages(db, tournament_names=tournaments)

@app.get("/api/stats")
def get_hero_stats_endpoint(
    db: Session = Depends(get_db),
    tournaments: Optional[List[str]] = Query(None),
    stages: Optional[List[str]] = Query(None),
    teams: Optional[List[str]] = Query(None)
):
    """
    The main API endpoint to get hero statistics.
    It accepts optional lists of tournaments, stages, and teams to filter the results.
    """
    return crud.get_hero_stats(
        db, 
        tournament_names=tournaments, 
        stage_names=stages, 
        team_names=teams
    )

@app.post("/webhooks/liquipedia")
async def receive_liquipedia_webhook(payload: schemas.LiquipediaWebhookPayload):
    """
    Receives a webhook notification from Liquipedia, determines the tournament,
    and triggers a background Celery task to refresh the data for that tournament.
    """
    print(f"Received webhook for page: {payload.page}")
    
    try:
        parts = payload.page.split('/')
        if parts[0] == "MPL":
            tournament_name = f"{parts[0]} {parts[1]} Season {parts[2]}"
        elif parts[0] == "MSC":
            tournament_name = f"{parts[0]} {parts[1]}"
        else:
            # Fallback for other tournament structures
            tournament_name = parts[0].replace('_', ' ')
    except Exception:
        tournament_name = "Unknown Tournament"

    # Trigger the Celery task to run in the background.
    # .delay() is how you send a job to the Celery worker.
    process_liquipedia_update.delay(payload.page, tournament_name)
    
    return {"message": "Webhook received and task queued."}
