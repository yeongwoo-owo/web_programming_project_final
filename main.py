from time import mktime
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Depends, Form, Request, Header, Path, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session
from sqlmodel import create_engine
from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse, FileResponse
from starlette.status import HTTP_201_CREATED
from starlette.websockets import WebSocket, WebSocketDisconnect

from crud.chat import create_text_chat, find_chats_by_chatroom, find_recent_chat_by_chatroom, create_image_chat
from crud.chatroom import create_chatroom, find_chatrooms_by_user, find_or_create_single_chatroom, find_chatroom_by_id
from crud.image import create_image, find_image_by_id
from crud.user import create_user, login_user, find_by_session_id, find_by_id, add_friend_relation, find_friends, \
    find_by_name
from exception.user_exceptions import SessionNotFoundException, LoginException, DuplicateUserException
from init.init import init_db
from websocket.connection_manager import manager

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
        init_db(session)


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
    whitelist = ["/login", "/register", "/static", "/favicon.ico", "/images"]
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
    print(user)
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


@app.get("/chatrooms")
def get_chatrooms(request: Request,
                  user_id: Annotated[int | None, Header()],
                  session: Session = Depends(session)):
    user = find_by_id(session, user_id)
    chatrooms = find_chatrooms_by_user(session, user)
    chatroom_list = []
    for chatroom in chatrooms:
        recent_chat = find_recent_chat_by_chatroom(session, chatroom)
        chatroom = jsonable_encoder(chatroom)

        if recent_chat:
            time = recent_chat.date_time()
            chat_type = recent_chat.chat_type()
            chat = jsonable_encoder(recent_chat)
            chat["time_string"] = parse_time(time)
            chat["time"] = time

            if chat_type == "image":
                chat["text"] = "사진"
            elif chat_type == "video":
                chat["text"] = "비디오"

            chatroom["recent_chat"] = chat
        else:
            chatroom["recent_chat"] = None

        chatroom_list.append(chatroom)
    print(chatroom_list)
    chatroom_list.sort(key=lambda x: -mktime(x["recent_chat"]["time"].timetuple()) if x["recent_chat"] else -1)
    return templates.TemplateResponse("chatroom_list.html",
                                      {"request": request, "chatrooms": chatroom_list, "tab": "chat"})


def parse_time(date):
    hour = date.hour
    minute = date.minute
    a = "오후" if hour >= 12 else "오전"
    hour = (hour - 1) % 12 + 1
    return f'{a} {hour}:{minute:0>2}'


@app.get("/chatrooms/{chatroom_id}")
def get_chatroom(request: Request,
                 user_id: Annotated[int | None, Header()],
                 chatroom_id: Annotated[int | None, Path()],
                 session: Session = Depends(session)):
    user = find_by_id(session, user_id)
    chatroom = find_chatroom_by_id(session, chatroom_id, user)
    return templates.TemplateResponse("chatroom.html", {"request": request, "chatroom": chatroom})


@app.get("/single-chats/{friend_id}")
def get_single_chat(user_id: Annotated[int | None, Header()],
                    friend_id: Annotated[int | None, Path()],
                    session: Session = Depends(session)):
    user = find_by_id(session, user_id)
    friend = find_by_id(session, friend_id)
    chatroom = find_or_create_single_chatroom(session, user, friend)
    return RedirectResponse("/chatrooms/" + str(chatroom.id), status_code=302)


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
    return JSONResponse({"chatroom_id": chatroom.id, "redirect_url": "/chatrooms/" + str(chatroom.id)})


@app.get("/chatrooms/{chatroom_id}/chats")
def get_chats(user_id: Annotated[int | None, Header()],
              chatroom_id: Annotated[int | None, Path()],
              session: Session = Depends(session)):
    user = find_by_id(session, user_id)
    chatroom = find_chatroom_by_id(session, chatroom_id, user)
    chats = find_chats_by_chatroom(session, chatroom)
    chat_list = []
    for chat in chats:
        chat_type = chat.chat_type()
        c = jsonable_encoder(chat)
        c["chat_type"] = chat_type
        c['writer'] = find_by_id(session, c['writer_id'])

        if chat_type == "image" or chat_type == "video":
            image = find_image_by_id(session, c['image_id'])
            c['image'] = jsonable_encoder(image)

        chat_list.append(c)
    print(chat_list)
    return JSONResponse({"login_user": user.id, "chatroom_id": chatroom.id, "chats": jsonable_encoder(chat_list)})


@app.websocket("/ws/connect")
async def ws_connect(ws: WebSocket, session: Session = Depends(session)):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            chat_type = data["chat_type"]
            writer = find_by_id(session, data["writer_id"])
            chatroom = find_chatroom_by_id(session, data["chatroom_id"], writer)

            if chat_type == "text":
                chat = jsonable_encoder(create_text_chat(session, chatroom, writer, data["text"]))
                chat['writer'] = find_by_id(session, writer.id)
                chat['chat_type'] = 'text'
                await manager.broadcast(jsonable_encoder(chat))

            elif chat_type == "image":
                image_id = data['image_id']
                image = find_image_by_id(session, image_id)
                encoded_image = jsonable_encoder(image)
                chat = jsonable_encoder(create_image_chat(session, chatroom, writer, image))
                chat['writer'] = find_by_id(session, writer.id)
                chat['image'] = encoded_image
                chat['chat_type'] = encoded_image["image_type"]
                print(f'{chat=}')
                await manager.broadcast(jsonable_encoder(chat))

    except WebSocketDisconnect as e:
        print(e)
    finally:
        await manager.disconnect(ws)


@app.post("/images")
async def upload_image(file: UploadFile,
                       session: Session = Depends(session)):
    image = await create_image(session, file, "./static")
    return JSONResponse(jsonable_encoder(image))


@app.get("/images/{image_name}")
async def download_image(image_name: Annotated[str | None, Path()]):
    return FileResponse("./static/image/" + image_name)


if __name__ == "__main__":
    uvicorn.run(app)
