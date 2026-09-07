from datetime import datetime

from pydantic import Field

from src.posts.constants import TITLE_MAX_LENGTH, PostStatus
from src.schemas import AppBaseModel


class PostCreate(AppBaseModel):
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    body: str = Field(min_length=1)


class PostRead(AppBaseModel):
    id: int
    title: str
    body: str
    status: PostStatus
    created_at: datetime
    published_at: datetime | None
