from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class ChatRoom(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = ""

    members: List["ChatRoomMember"] = Relationship(back_populates="chatroom")


class ChatRoomMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chatroom_id: Optional[int] = Field(default=None, foreign_key="chatroom.id")
    member_id: Optional[int] = Field(default=None, foreign_key="user.id")

    chatroom: Optional["ChatRoom"] = Relationship(back_populates="members")
    member: Optional["User"] = Relationship()
