from datetime import datetime

from sqlmodel import Session, select

from domain.chat import TextChat, ImageChat
from domain.chat_room import ChatRoom
from domain.image import Image
from domain.user import User


def create_text_chat(session: Session, chatroom: ChatRoom, writer: User, text: str):
    chat = TextChat(time=datetime.now().isoformat(), chatroom=chatroom, writer=writer, text=text)
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat


def create_image_chat(session: Session, chatroom: ChatRoom, writer: User, image: Image):
    chat = ImageChat(time=datetime.now().isoformat(), chatroom=chatroom, writer=writer, image=image)
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat


def time_string():
    return ("오전" if datetime.now().strftime("%p") == "AM" else "오후") + datetime.now().strftime(" %I:%M")


def find_chats_by_chatroom(session: Session, chatroom: ChatRoom):
    textchats = list(session.exec(select(TextChat).where(TextChat.chatroom == chatroom)).all())
    imagechats = list(session.exec(select(ImageChat).where(ImageChat.chatroom == chatroom)).all())
    return sorted(textchats + imagechats, key=lambda x: x.date_time())


def find_recent_chat(session: Session, chatroom: ChatRoom):
    chats = find_chats_by_chatroom(session, chatroom)
    return chats[-1] if chats else None
