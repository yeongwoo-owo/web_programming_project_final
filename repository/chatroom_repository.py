from sqlmodel import Session, select

from domain.chat_room import ChatRoom, ChatRoomMember
from domain.user import User


def create_group_chat(session: Session, members: list, name: str = "") -> ChatRoom:
    chatroom = ChatRoom(name=name)
    session.add(chatroom)
    for member in members:
        user = ChatRoomMember(chatroom=chatroom, member=member)
        session.add(user)
    session.commit()
    session.refresh(chatroom)
    return chatroom


def find_by_user(session: Session, user: User) -> list:
    chatroom_members = session.exec(select(ChatRoomMember).where(ChatRoomMember.member == user)).all()
    return list(map(lambda x: set_chatroom_name(x.chatroom, user), chatroom_members))


def get_single_chat(session: Session, user: User, other: User) -> ChatRoom:
    chatrooms = list(session.exec(select(ChatRoom)).all())
    for chatroom in chatrooms:
        chatroom_members = list(map(lambda x: x.member, chatroom.members))
        if len(chatroom_members) != 2:
            continue

        if user in chatroom_members and other in chatroom_members:
            return chatroom

    return create_group_chat(session, [user, other])


def find_by_id(session: Session, chatroom_id: int, user: User) -> ChatRoom:
    chatroom = session.exec(select(ChatRoom).where(ChatRoom.id == chatroom_id)).first()
    return set_chatroom_name(chatroom, user)


def set_chatroom_name(chatroom: ChatRoom, user: User) -> ChatRoom:
    if not chatroom.name:
        members = list(map(lambda x: x.member, chatroom.members))
        members.remove(user)
        chatroom.name = ", ".join(map(lambda x: x.name, members))
    return chatroom
