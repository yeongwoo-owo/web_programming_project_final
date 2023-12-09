import os
from uuid import uuid4 as uuid

from fastapi import UploadFile
from sqlmodel import Session, select

from domain.image import Image


async def create_image(session: Session, file: UploadFile, base_dir: str):
    content = await file.read()
    image_path = base_dir + "/image"
    ext = parse_ext(file.content_type)

    image_name = str(uuid()) + ext

    with open(os.path.join(image_path, image_name), "wb") as fp:
        fp.write(content)

    image = Image(name=file.filename, image_name=image_name)
    session.add(image)
    session.commit()
    session.refresh(image)
    return image


def parse_ext(content_type):
    if content_type == "image/png":
        return ".png"


def find_image_by_id(session: Session, image_id: int):
    return session.exec(select(Image).where(Image.id == image_id)).first()
