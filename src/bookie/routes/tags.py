from collections.abc import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from bookie import crud, schemas
from bookie.database import get_session
from bookie.models import Tag

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=Sequence[schemas.TagRead])
async def get_all_tags(session: AsyncSession = Depends(get_session)) -> Sequence[Tag]:
    return await crud.get_all_tags(session)


@router.get("/{tag_id}", response_model=schemas.TagRead)
async def get_tag(
    tag_id: UUID, session: AsyncSession = Depends(get_session)
) -> Tag | None:
    tag = await crud.get_tag(session, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag doesn't exist")
    return tag
