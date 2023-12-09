import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class Chat(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    chatroom_id: Optional[int] = Field(default=None, foreign_key="chatroom.id")
    writer_id: Optional[int] = Field(default=None, foreign_key="user.id")
    time: str

    def date_time(self):
        return datetime.datetime.fromisoformat(self.time)

    def chat_type(self):
        pass


class TextChat(Chat, table=True):
    text: str

    chatroom: Optional["ChatRoom"] = Relationship()
    writer: Optional["User"] = Relationship()

    def chat_type(self):
        return "text"


class ImageChat(Chat, table=True):
    image_id: Optional[int] = Field(default=None, foreign_key="image.id")

    chatroom: Optional["ChatRoom"] = Relationship()
    writer: Optional["User"] = Relationship()
    image: Optional["Image"] = Relationship()

    def chat_type(self):
        return self.image.image_type
