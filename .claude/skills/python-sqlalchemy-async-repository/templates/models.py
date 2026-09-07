from datetime import UTC, datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.posts.constants import TITLE_MAX_LENGTH, PostStatus


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH), index=True)
    body: Mapped[str] = mapped_column(String())
    status: Mapped[PostStatus] = mapped_column(String(16), default=PostStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    def publish(self) -> None:
        self.status = PostStatus.PUBLISHED
        self.published_at = datetime.now(UTC)
