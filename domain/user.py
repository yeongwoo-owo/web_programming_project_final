from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class UserBase(SQLModel):
    name: str
    login_id: str
    password: str


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    session: Optional["UserSession"] = Relationship(back_populates="user")
