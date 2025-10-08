# In app/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

# This schema now perfectly matches the Liquipedia documentation for edit events.
class LiquipediaWebhookPayload(BaseModel):
    page: str
    namespace: int
    wiki: str
    event: str