from uuid import uuid4 as uuid

from sqlmodel import Session, select

from domain.user import User
from domain.user_session import UserSession


def exist_by_id(session: Session, login_id: str) -> bool:
    return session.exec(select(User).where(User.login_id == login_id)).first() is not None


def create_user(session: Session, name: str, login_id: str, password: str) -> User:
    if exist_by_id(session, login_id):
        raise RuntimeError('User login id 중복')

    user = User(name=name, login_id=login_id, password=password)
    user.session = UserSession()
    session.add(user)
    session.commit()
    return user


def login_user(session: Session, login_id: str, password: str) -> User:
    user = session.exec(select(User).where(User.login_id == login_id and User.password == password)).first()
    if not user:
        raise RuntimeError("유저 없음")

    user.session.session_id = str(uuid())
    session.add(user)
    session.commit()
    return user


def find_by_id(session: Session, user_id: int) -> User:
    return session.exec(select(User).where(User.id == user_id)).first()


def find_by_session_id(session: Session, session_id: str) -> User | None:
    user_session = session.exec(select(UserSession).where(UserSession.session_id == session_id)).first()
    if not user_session:
        return None
    return user_session.user
