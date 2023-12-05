from sqlmodel import Session, select

from domain.ChatRoom import ChatRoom, ChatRoomMember
from domain.user import User


def create_chat(session: Session, members: list, name: str = "") -> ChatRoom:
    chatroom = ChatRoom(name=name)
    session.add(chatroom)
    for member in members:
        user = ChatRoomMember(chatroom=chatroom, member=member)
        session.add(user)
    session.commit()
    return chatroom


def find_chat_rooms_by_user(session: Session, user: User) -> list:
    chat_room_members = session.exec(select(ChatRoomMember).where(ChatRoomMember.member == user)).all()
    chatrooms = list(map(lambda x: x.chatroom, chat_room_members))

    for chatroom in chatrooms:
        if not chatroom.name:
            members = list(map(lambda x: x.member, chatroom.members))
            members.remove(user)
            chatroom.name = ", ".join(map(lambda x: x.name, members))

    return chatrooms
