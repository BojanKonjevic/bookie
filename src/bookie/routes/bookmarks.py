from collections.abc import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from bookie import crud, schemas
from bookie.database import get_session
from bookie.models import Bookmark

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.get("", response_model=Sequence[schemas.BookmarkRead])
async def get_all_bookmarks(
    session: AsyncSession = Depends(get_session),
) -> Sequence[Bookmark]:
    return await crud.get_all_bookmarks(session)


@router.get("/{bookmark_id}", response_model=schemas.BookmarkRead)
async def get_bookmark(
    bookmark_id: UUID, session: AsyncSession = Depends(get_session)
) -> Bookmark | None:
    bookmark = await crud.get_bookmark(session, bookmark_id)
    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark doesn't exist")
    return bookmark


@router.post("", response_model=schemas.BookmarkRead)
async def create_bookmark(
    bookmark: schemas.BookmarkCreate, session: AsyncSession = Depends(get_session)
) -> Bookmark:
    return await crud.create_bookmark(session, bookmark)


@router.delete("/{bookmark_id}", status_code=204)
async def delete_bookmark(
    bookmark_id: UUID, session: AsyncSession = Depends(get_session)
) -> None:
    status = await crud.delete_bookmark(session, bookmark_id)
    if not status:
        raise HTTPException(status_code=404, detail="Bookmark doesn't exist")


@router.patch("/{bookmark_id}", response_model=schemas.BookmarkRead)
async def update_bookmark(
    bookmark_id: UUID,
    bookmark_update: schemas.BookmarkUpdate,
    session: AsyncSession = Depends(get_session),
) -> Bookmark | None:
    bookmark = await crud.update_bookmark(session, bookmark_id, bookmark_update)
    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark doesn't exist")
    return bookmark
