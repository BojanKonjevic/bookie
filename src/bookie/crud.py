from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bookie.models import Bookmark, RefreshToken, Tag, User
from bookie.schemas import BookmarkCreate, BookmarkUpdate
from bookie.security import generate_refresh_token, hash_password
from bookie.settings import settings


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, email: str, password: str) -> User:
    user = User(email=email, hashed_password=hash_password(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_refresh_token(session: AsyncSession, user_id: UUID) -> RefreshToken:
    token = RefreshToken(
        token=generate_refresh_token(),
        user_id=user_id,
        expires_at=datetime.now(UTC).replace(tzinfo=None)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token


async def get_refresh_token(session: AsyncSession, token: str) -> RefreshToken | None:
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token == token)
    )
    return result.scalar_one_or_none()


async def revoke_refresh_token(session: AsyncSession, token: str) -> bool:
    db_token = await get_refresh_token(session, token)
    if db_token is None:
        return False
    db_token.revoked = True
    await session.commit()
    return True


async def create_bookmark(
    session: AsyncSession, bookmark: BookmarkCreate, user_id: UUID
) -> Bookmark:
    tag_names = set(bookmark.tags)
    result = await session.execute(
        select(Tag).where((Tag.name.in_(tag_names)), Tag.user_id == user_id)
    )
    existing_tags = {tag.name: tag for tag in result.scalars()}
    tags = []
    for tag_name in tag_names:
        tag = existing_tags.get(tag_name)
        if not tag:
            tag = Tag(name=tag_name, user_id=user_id)
        tags.append(tag)

    db_bookmark = Bookmark(
        title=bookmark.title,
        url=str(bookmark.url),
        description=bookmark.description,
        favorite=bookmark.favorite,
        tags=tags,
        user_id=user_id,
    )

    session.add(db_bookmark)
    try:
        await session.commit()
    except IntegrityError as err:
        await session.rollback()
        raise ValueError("URL already exists") from err
    await session.refresh(db_bookmark, ["tags"])
    return db_bookmark


async def get_all_bookmarks(
    session: AsyncSession,
    user_id: UUID,
    favorite: bool | None = None,
    tag_names: Sequence[str] | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> Sequence[Bookmark]:
    query = (
        select(Bookmark)
        .where(Bookmark.user_id == user_id)
        .options(selectinload(Bookmark.tags))
    )
    if favorite is not None:
        query = query.where(Bookmark.favorite == favorite)
    if tag_names is not None:
        query = query.where(Bookmark.tags.any(Tag.name.in_(tag_names)))
    if search is not None:
        query = query.where(
            or_(
                Bookmark.title.ilike(f"%{search}%"),
                Bookmark.description.ilike(f"%{search}%"),
            )
        )
    result = await session.execute(query.offset((page - 1) * limit).limit(limit))
    return result.scalars().all()


async def get_bookmark(
    session: AsyncSession, bookmark_id: UUID, user_id: UUID
) -> Bookmark | None:
    result = await session.execute(
        select(Bookmark)
        .where((Bookmark.id == bookmark_id), (Bookmark.user_id == user_id))
        .options(selectinload(Bookmark.tags))
    )
    return result.scalar_one_or_none()


async def update_bookmark(
    session: AsyncSession,
    bookmark_id: UUID,
    bookmark_update: BookmarkUpdate,
    user_id: UUID,
) -> Bookmark | None:
    db_bookmark = (
        await session.execute(
            select(Bookmark).where(
                (Bookmark.id == bookmark_id), (Bookmark.user_id == user_id)
            )
        )
    ).scalar_one_or_none()
    if not db_bookmark:
        return None
    update_data = bookmark_update.model_dump(exclude_unset=True)
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])

    tags = update_data.pop("tags", None)
    if tags is not None:
        tag_names = set(tags)
        result = await session.execute(
            select(Tag).where(Tag.name.in_(tag_names), Tag.user_id == user_id)
        )
        existing_tags = {tag.name: tag for tag in result.scalars()}
        new_tags = []
        for tag_name in tag_names:
            tag = existing_tags.get(tag_name)
            if not tag:
                tag = Tag(name=tag_name, user_id=user_id)
            new_tags.append(tag)
        db_bookmark.tags = new_tags

    for field, value in update_data.items():
        setattr(db_bookmark, field, value)
    await session.commit()
    await session.refresh(db_bookmark, ["tags"])
    return db_bookmark


async def delete_bookmark(
    session: AsyncSession, bookmark_id: UUID, user_id: UUID
) -> bool:
    db_bookmark = (
        await session.execute(
            select(Bookmark)
            .where((Bookmark.id == bookmark_id), (Bookmark.user_id == user_id))
            .options(selectinload(Bookmark.tags).selectinload(Tag.bookmarks))
        )
    ).scalar_one_or_none()
    if not db_bookmark:
        return False
    for tag in db_bookmark.tags:
        if len([b for b in tag.bookmarks if b.user_id == user_id]) == 1:
            await session.delete(tag)
    await session.delete(db_bookmark)
    await session.commit()
    return True


async def get_all_tags(session: AsyncSession, user_id: UUID) -> Sequence[Tag]:
    result = await session.execute(select(Tag).where(Tag.user_id == user_id))
    return result.scalars().all()


async def get_tag(session: AsyncSession, tag_id: UUID, user_id: UUID) -> Tag | None:
    result = await session.execute(
        select(Tag).where((Tag.id == tag_id), (Tag.user_id == user_id))
    )
    return result.scalar_one_or_none()
