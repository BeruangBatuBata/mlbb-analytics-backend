# In app/schemas.py
from pydantic import BaseModel
from typing import Optional, List

class LiquipediaWebhookPayload(BaseModel):
    page: str
    namespace: int
    wiki: str
    event: str

class Tournament(BaseModel):
    id: int
    name: str
    region: Optional[str] = None

    class Config:
        from_attributes = True

class Team(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

# --- NEW SCHEMAS START ---

class HeroPerformanceByTeam(BaseModel):
    team_name: str
    games_played: int
    wins: int
    win_rate: float

class HeroPerformanceVsOpponent(BaseModel):
    opponent_hero_name: str
    games_faced: int
    wins_against: int
    win_rate_vs: float

class HeroDetails(BaseModel):
    by_team: List[HeroPerformanceByTeam]
    vs_opponents: List[HeroPerformanceVsOpponent]

# --- NEW SCHEMAS END ---