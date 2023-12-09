from typing import Optional

from sqlmodel import SQLModel, Field


class Image(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    image_name: str
