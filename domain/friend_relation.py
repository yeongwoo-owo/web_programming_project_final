from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class FriendRelation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    friend_id: Optional[int] = Field(default=None, foreign_key="user.id")

    user: Optional["User"] = Relationship(
        sa_relationship_kwargs={"primaryjoin": "User.id==FriendRelation.user_id", "lazy": "joined"}
    )
    friend: Optional["User"] = Relationship(
        sa_relationship_kwargs={"primaryjoin": "User.id==FriendRelation.friend_id", "lazy": "joined"}
    )
