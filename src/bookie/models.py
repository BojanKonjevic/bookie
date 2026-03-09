from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

bookmark_tags = Table(
    "bookmark_tags",
    Base.metadata,
    Column(
        "bookmark_id", ForeignKey("bookmarks.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    tags: Mapped[list[Tag]] = relationship(
        secondary=bookmark_tags, back_populates="bookmarks"
    )


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, unique=True)
    bookmarks: Mapped[list[Bookmark]] = relationship(
        secondary=bookmark_tags, back_populates="tags"
    )
