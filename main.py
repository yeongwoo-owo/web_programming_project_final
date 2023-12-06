from typing import Annotated

import uvicorn
from fastapi import FastAPI, Depends, Form, Request, Header, Path
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, select
from sqlmodel import create_engine
from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.status import HTTP_201_CREATED

from crud.chatroom import create_chatroom, find_chatrooms_by_user, find_or_create_single_chatroom, find_chatroom_by_id
from crud.user import create_user, login_user, find_by_session_id, find_by_id, add_friend_relation, find_friends, \
    find_by_name
from domain.ChatRoom import ChatRoomMember, ChatRoom
from domain.friend_relation import FriendRelation
from domain.user import User
from domain.user_session import UserSession
from exception.user_exceptions import SessionNotFoundException, LoginException, DuplicateUserException

app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
templates = Jinja2Templates(directory="templates")
engine = create_engine("sqlite:///database.db")


def session():
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def setup():
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
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
        session.commit()

        user = create_user(session, "유저", "user", "user")
        for i in range(1, 21):
            s = "user" + str(i)
            name = "유저" + str(i)
            u = create_user(session, name, s, s)
            if i % 2 == 0:
                add_friend_relation(session, user, u)
                if i % 3 == 0:
                    create_chatroom(session, members=[user, u])
        userA = create_user(session, "유저A", "userA", "userA")
        userB = create_user(session, "유저B", "userB", "userB")
        userC = create_user(session, "유저C", "userC", "userC")
        userD = create_user(session, "유저D", "userD", "userD")
        userE = create_user(session, "유저E", "userE", "userE")
        add_friend_relation(session, user, userA)
        add_friend_relation(session, user, userB)
        add_friend_relation(session, user, userC)
        create_chatroom(session, [user, userA, userB, userC, userD, userE])


# TODO: PRG 적용
@app.exception_handler(DuplicateUserException)
def login_exception_handler(request: Request, error: DuplicateUserException):
    return templates.TemplateResponse("register_form.html", {"request": request, "error": error.description()})


@app.exception_handler(LoginException)
def login_exception_handler(request: Request, error: LoginException):
    return templates.TemplateResponse("login_form.html", {"request": request, "error": error.description()})


def update_header(request: Request, key, value):
    header = MutableHeaders(request._headers)
    header[key] = str(value)
    request._headers = header
    request.scope.update(headers=request._headers.raw)
    return request


def is_whitelist(path):
    whitelist = ["/login", "/register", "/static", "/favicon.ico"]
    for url in whitelist:
        if path.startswith(url):
            return True
    return False


@app.middleware("http")
async def authentication_filter(request: Request, call_next):
    path = request.url.path

    if not is_whitelist(path):
        if "session_id" not in request.cookies:
            print("세션이 존재하지 않습니다.")
            return RedirectResponse(url="/login", status_code=302)

        try:
            with Session(engine) as session:
                session_id = request.cookies["session_id"]
                user = find_by_session_id(session, session_id)
                request = update_header(request, key="user-id", value=user.id)
        except SessionNotFoundException as e:
            print(e)
            return RedirectResponse(url="/login", status_code=302)

    return await call_next(request)


@app.get("/register")
def register_user_form(request: Request):
    return templates.TemplateResponse("register_form.html", {"request": request})


@app.post("/register")
def register_user(name: str = Form(),
                  login_id: str = Form(),
                  password: str = Form(),
                  session: Session = Depends(session)):
    user = create_user(session, name=name, login_id=login_id, password=password)
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="session_id", value=user.session.session_id)
    return response


@app.get("/login")
def login_user_form(request: Request):
    return templates.TemplateResponse("login_form.html", {"request": request})


@app.post("/login")
def login(login_id: str = Form(),
          password: str = Form(),
          session: Session = Depends(session)):
    user = login_user(session, login_id, password)
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="session_id", value=user.session.session_id)
    return response


@app.get("/")
def home(request: Request,
         user_id: Annotated[int | None, Header()],
         session: Session = Depends(session)):
    user = find_by_id(session, user_id)
    friends = find_friends(session, user)
    return templates.TemplateResponse("home.html",
                                      {"request": request, "user": user, "friends": friends, "tab": "home"})


@app.get("/friends")
def add_friend_form(request: Request):
    return templates.TemplateResponse("add_friend.html", {"request": request})


@app.post("/friends/{friend_id}", status_code=HTTP_201_CREATED)
def add_friend(user_id: Annotated[int | None, Header()],
               friend_id: Annotated[int | None, Path()],
               session: Session = Depends(session)):
    user = find_by_id(session, user_id)
    friend = find_by_id(session, friend_id)
    add_friend_relation(session, user, friend)


@app.get("/users")
def search_users(user_id: Annotated[int | None, Header()],
                 query: str = "",
                 session: Session = Depends(session)):
    users = find_by_name(session, query)
    user = find_by_id(session, user_id)
    friends = find_friends(session, user)
    if user in users:
        users.remove(user)
    users = sorted(list(map(lambda x: {"user": x, "is_friend": x in friends}, users)), key=lambda x: x["is_friend"])
    return JSONResponse({"result": jsonable_encoder(users)})


@app.get("/chats")
def get_chatrooms(request: Request,
                  user_id: Annotated[int | None, Header()],
                  session: Session = Depends(session)):
    user = find_by_id(session, user_id)
    chatrooms = find_chatrooms_by_user(session, user)
    return templates.TemplateResponse("chatroom_list.html", {"request": request, "chatrooms": chatrooms, "tab": "chat"})


@app.get("/chats/{chat_id}")
def get_chatroom(request: Request,
                 user_id: Annotated[int | None, Header()],
                 chat_id: Annotated[int | None, Path()],
                 session: Session = Depends(session)):
    user = find_by_id(session, user_id)
    chatroom = find_chatroom_by_id(session, chat_id, user)
    return templates.TemplateResponse("chatroom.html", {"request": request, "chatroom": chatroom})


@app.get("/single-chats/{friend_id}")
def get_single_chat(user_id: Annotated[int | None, Header()],
                    friend_id: Annotated[int | None, Path()],
                    session: Session = Depends(session)):
    user = find_by_id(session, user_id)
    friend = find_by_id(session, friend_id)
    chatroom = find_or_create_single_chatroom(session, user, friend)
    return RedirectResponse("/chats/" + str(chatroom.id), status_code=302)


@app.get("/groupchat")
def create_group_chat_form(request: Request,
                           user_id: Annotated[int | None, Header()],
                           session: Session = Depends(session)):
    user = find_by_id(session, user_id)
    friends = find_friends(session, user)
    return templates.TemplateResponse("create_chat.html", {"request": request, "friends": friends})


class CreateGroupChatRequest(SQLModel):
    name: str | None
    member_ids: list | None


@app.post("/groupchat")
def create_group_chat(user_id: Annotated[int | None, Header()],
                      dto: CreateGroupChatRequest,
                      session: Session = Depends(session)):
    print(dto)
    user = find_by_id(session, user_id)
    members = list(map(lambda x: find_by_id(session, x), dto.member_ids))
    chatroom = create_chatroom(session, members + [user], dto.name)
    return JSONResponse({"chatroom_id": chatroom.id, "redirect_url": "/chats/" + str(chatroom.id)})


if __name__ == "__main__":
    uvicorn.run(app)
