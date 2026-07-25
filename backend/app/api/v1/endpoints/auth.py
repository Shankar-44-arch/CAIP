"""CAIP-Karnataka — Auth Endpoints"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import (create_access_token, create_refresh_token,
                                hash_password, verify_password)
from app.models.orm_models import AppUser
from app.schemas.schemas import LoginRequest, Token, UserCreate, UserOut
from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(AppUser).where(AppUser.email == payload.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = AppUser(
        email=payload.email, username=payload.username, full_name=payload.full_name,
        role=payload.role.value, hashed_pw=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserOut(id=str(user.id), email=user.email, username=user.username,
                    full_name=user.full_name, role=user.role)


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(AppUser).where(AppUser.username == payload.username))).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_pw):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    user.last_login = datetime.now(timezone.utc)
    await db.flush()

    return Token(
        access_token=create_access_token(str(user.id), user.role),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(AppUser).where(AppUser.id == current_user["id"]))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(id=str(user.id), email=user.email, username=user.username,
                    full_name=user.full_name, role=user.role)
