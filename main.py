from typing import Annotated

import uvicorn
from fastapi import FastAPI, Depends, Form, Request, Header
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, select
from sqlmodel import create_engine
from starlette.datastructures import MutableHeaders

from crud.user import create_user, login_user, find_by_session_id, find_by_id
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
        session.commit()


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
    return templates.TemplateResponse("home.html", {"request": request, "user": user})


if __name__ == "__main__":
    uvicorn.run(app)
