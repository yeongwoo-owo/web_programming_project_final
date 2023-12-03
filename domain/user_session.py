from typing import Optional
from uuid import uuid4 as uuid

from sqlmodel import SQLModel, Field, Relationship


class UserSessionBase(SQLModel):
    session_id: str = Field(default=str(uuid()))
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")


class UserSession(UserSessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    user: Optional["User"] = Relationship(back_populates="session")
