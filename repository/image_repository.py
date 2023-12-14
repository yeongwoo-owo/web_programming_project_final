import os
from uuid import uuid4 as uuid

from fastapi import UploadFile
from sqlmodel import Session, select

from domain.image import Image


async def create(session: Session, file: UploadFile, base_dir: str):
    image_path = base_dir + "/image"
    create_dir(image_path)

    content = await file.read()
    ext = parse_ext(file.content_type)

    image_name = str(uuid()) + ext

    with open(os.path.join(image_path, image_name), "wb") as fp:
        fp.write(content)

    image = Image(name=file.filename, image_name=image_name, image_type=get_type(file.content_type))
    session.add(image)
    session.commit()
    session.refresh(image)
    return image


def create_dir(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        print("폴더 생성 불가")


def parse_ext(content_type):
    return '.' + content_type.split("/")[1]


def get_type(content_type):
    return content_type.split("/")[0]


def find_by_id(session: Session, image_id: int):
    return session.exec(select(Image).where(Image.id == image_id)).first()
