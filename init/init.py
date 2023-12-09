from sqlmodel import select
from crud.chat import create_text_chat
from crud.chatroom import create_chatroom
from crud.user import create_user, add_friend_relation
from domain.chat import TextChat
from domain.chat_room import ChatRoomMember, ChatRoom
from domain.friend_relation import FriendRelation
from domain.user import User
from domain.user_session import UserSession


def init_db(session):
    for user in session.exec(select(User)).all():
        session.delete(user)
    for user_session in session.exec(select(UserSession)).all():
        session.delete(user_session)
    for friend in session.exec(select(FriendRelation)).all():
        session.delete(friend)
    for member in session.exec(select(ChatRoomMember)).all():
        session.delete(member)
    for room in session.exec(select(ChatRoom)).all():
        session.delete(room)
    for chat in session.exec(select(TextChat)).all():
        session.delete(chat)
    session.commit()

    user = create_user(session, "유저", "user", "user")
    for i in range(1, 21):
        s = "user" + str(i)
        name = "유저" + str(i)
        u = create_user(session, name, s, s)
        if i % 2 == 0:
            add_friend_relation(session, user, u)
    userA = create_user(session, "유저A", "userA", "userA")
    userB = create_user(session, "유저B", "userB", "userB")
    userC = create_user(session, "유저C", "userC", "userC")
    userD = create_user(session, "유저D", "userD", "userD")
    userE = create_user(session, "유저E", "userE", "userE")
    add_friend_relation(session, user, userA)
    add_friend_relation(session, user, userB)
    add_friend_relation(session, user, userC)
    chatroom = create_chatroom(session, [user, userA, userB, userC, userD, userE])
    create_text_chat(session, chatroom, user, "안녕")
    create_text_chat(session, chatroom, userA, "안녕하세요")
