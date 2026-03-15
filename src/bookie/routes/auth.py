from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, schemas
from ..database import get_session
from ..security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserRead, status_code=201)
async def register(
    body: schemas.UserRegister, session: AsyncSession = Depends(get_session)
) -> schemas.UserRead:
    existing = await crud.get_user_by_email(session, body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email not available")
    user = await crud.create_user(session, body.email, body.password)
    return schemas.UserRead.model_validate(user)


@router.post("/token", response_model=schemas.Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> schemas.Token:
    user = await crud.get_user_by_email(session, form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_access_token(user.id)
    return schemas.Token(access_token=token)
