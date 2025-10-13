# In app/models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    JSON,
    Boolean
)
from sqlalchemy.orm import relationship, declarative_base

# This is the base class that all our database models will inherit from.
Base = declarative_base()

# --- Core Models ---

class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # --- NEW COLUMNS START ---
    region = Column(String, index=True)
    split = Column(String, index=True) 
    # --- NEW COLUMNS END ---

    matches = relationship("Match", back_populates="tournament")

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
class Hero(Base):
    __tablename__ = "heroes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    # The unique ID from Liquipedia to prevent duplicate entries.
    liquipedia_id = Column(Integer, nullable=False) 
    
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    
    team1_id = Column(Integer, ForeignKey("teams.id"))
    team2_id = Column(Integer, ForeignKey("teams.id"))
    winner_id = Column(Integer, ForeignKey("teams.id"))

    team1_score = Column(Integer)
    team2_score = Column(Integer)
    
    match_date = Column(DateTime)
    
    # Store the original full JSON payload from the API for future analysis.
    details = Column(JSON) 
    
    # --- Relationships ---
    # These link the match back to its related objects.
    tournament = relationship("Tournament", back_populates="matches")
    team1 = relationship("Team", foreign_keys=[team1_id])
    team2 = relationship("Team", foreign_keys=[team2_id])
    winner = relationship("Team", foreign_keys=[winner_id])

    # This links a match to all its associated pick/ban records.
    heroes = relationship("MatchHero", back_populates="match", cascade="all, delete-orphan")


# In app/models.py

# ... (Tournament, Team, Hero, and Match classes are the same) ...

# --- Association Table for Picks/Bans ---
class MatchHero(Base):
    __tablename__ = "match_heroes"
    match_id = Column(Integer, ForeignKey("matches.id"), primary_key=True)
    hero_id = Column(Integer, ForeignKey("heroes.id"), primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), primary_key=True)
    type = Column(String, primary_key=True) # 'pick' or 'ban'
    game_number = Column(Integer, primary_key=True)
    is_win = Column(Boolean)
    
    # --- ADD THIS NEW COLUMN ---
    side = Column(String) # Will store 'blue' or 'red'
    # ---------------------------

    match = relationship("Match", back_populates="heroes")
    hero = relationship("Hero")
    team = relationship("Team")