from datetime import datetime

from sqlmodel import Session, select

from domain.chat import TextChat
from domain.chat_room import ChatRoom
from domain.user import User


def create_text_chat(session: Session, chatroom: ChatRoom, writer: User, text: str):
    chat = TextChat(time=time_string(), chatroom=chatroom, writer=writer, text=text)
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat


def time_string():
    return ("오전" if datetime.now().strftime("%p") == "AM" else "오후") + datetime.now().strftime(" %I:%M")


def find_chats_by_chatroom(session: Session, chatroom: ChatRoom):
    return session.exec(select(TextChat).where(TextChat.chatroom == chatroom)).all()


def find_recent_chat_by_chatroom(session: Session, chatroom: ChatRoom):
    return session.exec(select(TextChat).where(TextChat.chatroom == chatroom).order_by(TextChat.id.desc())).first()
