import datetime
import uuid

from sqlalchemy import DateTime
from sqlmodel import Column, Field, SQLModel


def now_utc():
    return datetime.datetime.now(datetime.UTC)

class ProfileBase(SQLModel):
    display_name: str | None = Field(default=None, max_length=100)
    bio: str | None =Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=255)

class Profile(ProfileBase, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True, unique=True, nullable=False)
    created_at: datetime.datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=now_utc, nullable=False)
    )
    updated_at: datetime.datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)
    )
