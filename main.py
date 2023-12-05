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

from crud.user import create_user, login_user, find_by_session_id, find_by_id, add_friend_relation, find_friends, \
    find_by_name
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
        session.commit()

        user = create_user(session, "user", "user", "user")
        for i in range(1, 21):
            s = "user" + str(i)
            u = create_user(session, s, s, s)
            if i % 2 == 0:
                add_friend_relation(session, user, u)


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


if __name__ == "__main__":
    uvicorn.run(app)
