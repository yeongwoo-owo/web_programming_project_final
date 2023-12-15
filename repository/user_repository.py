from uuid import uuid4 as uuid

from sqlmodel import Session, select

from domain.friend_relation import FriendRelation
from domain.user import User
from domain.user_session import UserSession
from util.user_exceptions import SessionNotFoundException, LoginException, DuplicateUserException


def exist_by_id(session: Session, login_id: str) -> bool:
    return session.exec(select(User).where(User.login_id == login_id)).first() is not None


def create(session: Session, name: str, login_id: str, password: str) -> User:
    if exist_by_id(session, login_id):
        raise DuplicateUserException(login_id)

    user = User(name=name, login_id=login_id, password=password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def login(session: Session, login_id: str, password: str) -> User:
    user = session.exec(select(User).where(User.login_id == login_id and User.password == password)).first()
    if not user:
        raise LoginException()

    if not user.session:
        user.session = UserSession(session_id=str(uuid()))
    else:
        user.session.session_id = str(uuid())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def find_by_id(session: Session, user_id: int) -> User:
    return session.exec(select(User).where(User.id == user_id)).first()


def find_by_name(session: Session, user_name: str) -> list:
    return list(session.exec(select(User).where(User.name.contains(user_name))).all())


def find_by_session_id(session: Session, session_id: str) -> User:
    user_session = session.exec(select(UserSession).where(UserSession.session_id == session_id)).first()
    if not user_session:
        raise SessionNotFoundException(session_id)
    return user_session.user


def add_friend_relation(session: Session, user: User, friend: User):
    session.add(FriendRelation(user=user, friend=friend))
    session.commit()


def find_friends(session: Session, user: User) -> list:
    friends = session.exec(select(FriendRelation).where(FriendRelation.user == user)).all()
    return sorted(list(map(lambda x: x.friend, friends)), key=lambda x: x.name)
