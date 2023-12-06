from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class Chat(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    chatroom_id: Optional[int] = Field(default=None, foreign_key="chatroom.id")
    writer_id: Optional[int] = Field(default=None, foreign_key="user.id")
    time: str


class TextChat(Chat, table=True):
    text: str

    chatroom: Optional["ChatRoom"] = Relationship()
    writer: Optional["User"] = Relationship()
