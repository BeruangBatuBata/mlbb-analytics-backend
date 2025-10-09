# In app/schemas.py
from pydantic import BaseModel
from typing import Optional

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