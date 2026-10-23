"""User management using the persisted email-based account model."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.permissions import UserRole
from app.core.security import get_current_user, hash_password, require_role
from app.db.database import get_db
from app.models import AuditLog, User
from app.schemas import UserCreate as UserCreateRequest, UserResponse


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=1, max_length=255)
    is_active: bool | None = None
    role: UserRole | None = None

    model_config = {"extra": "forbid"}


class UserRoleUpdateRequest(BaseModel):
    role: UserRole


def record_user_change(db: Session, actor: User, user: User, action: str) -> None:
    db.add(AuditLog(
        actor_id=actor.id,
        action=action,
        action_category="user_management",
        target_type="user",
        target_id=str(user.id),
        action_status="success",
        changes_after={"role": user.role, "is_active": user.is_active}
        if action != "delete_user" else None,
    ))


def commit_user_change(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, detail="Email already exists or account is still referenced")
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Unable to save user change")
        raise HTTPException(500, detail="Unable to save user change")


def find_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, detail="User not found")
    return user


@router.get("/me", response_model=UserResponse)
async def current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    return db.query(User).order_by(User.id).offset(skip).limit(limit).all()


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    email = str(user_data.email).lower()
    name = user_data.full_name.strip()
    if not name:
        raise HTTPException(422, detail="Full name cannot be blank")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, detail="Email already exists")
    user = User(
        email=email, full_name=name,
        password_hash=hash_password(user_data.password),
        role=user_data.role, is_active=True,
    )
    try:
        db.add(user)
        db.flush()
        record_user_change(db, current_user, user, "create_user")
        commit_user_change(db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, detail="Email already exists")
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Unable to create user")
        raise HTTPException(500, detail="Unable to create user")
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(403, detail="Not authorized to view this user")
    return find_user(db, user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(403, detail="Not authorized to update this user")
    if current_user.role != UserRole.ADMIN and (
        user_data.role is not None or user_data.is_active is not None
    ):
        raise HTTPException(403, detail="Only admins can change account role or status")
    user = find_user(db, user_id)
    if user_data.email is not None:
        email = str(user_data.email).lower()
        if db.query(User).filter(User.email == email, User.id != user_id).first():
            raise HTTPException(409, detail="Email already exists")
        user.email = email
    if user_data.full_name is not None:
        if not user_data.full_name.strip():
            raise HTTPException(422, detail="Full name cannot be blank")
        user.full_name = user_data.full_name.strip()
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.role is not None:
        user.role = user_data.role
    record_user_change(db, current_user, user, "update_user")
    commit_user_change(db)
    db.refresh(user)
    return user


@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_data: UserRoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    return await update_user(
        user_id, UserUpdateRequest(role=role_data.role), db, current_user
    )


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    if current_user.id == user_id:
        raise HTTPException(400, detail="Cannot delete your own user account")
    user = find_user(db, user_id)
    record_user_change(db, current_user, user, "delete_user")
    db.delete(user)
    commit_user_change(db)
