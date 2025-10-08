# In app/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Database Connection Setup ---

# Get the database URL from environment variables
# This is a secure way to store sensitive information
# Example URL: postgresql://user:password@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL environment variable set")

# The 'engine' is the core interface to the database
# It manages the connections and interprets our commands
engine = create_engine(DATABASE_URL)

# A 'Session' is our "window" into the database.
# We will create a session every time we need to talk to the database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Dependency to Get DB Session ---

# This is a special function that FastAPI will use
# to provide a database session to our API endpoints.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()