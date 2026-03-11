from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bookie.database import Base

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
    title: Mapped[str] = mapped_column(String(255), index=True)
    url: Mapped[str] = mapped_column(String(2048), unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    favorite: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    tags: Mapped[list[Tag]] = relationship(
        secondary=bookmark_tags, back_populates="bookmarks", lazy="selectin"
    )


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    bookmarks: Mapped[list[Bookmark]] = relationship(
        secondary=bookmark_tags, back_populates="tags"
    )
