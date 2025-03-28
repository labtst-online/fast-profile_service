import uuid
from datetime import datetime

from sqlmodel import SQLModel


class ProfileUpdate(SQLModel):
    display_name: str | None
    bio: str | None
    avatar_url: str | None


class ProfileRead(ProfileUpdate): # Inherit fields from ProfileUpdate
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
