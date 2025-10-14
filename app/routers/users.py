from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.database.database import get_async_session
from app.database.models import User, Team, RoleEnum
from app.users import current_active_user
from app.schemas import UserRead, UserUpdate


router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(current_active_user)):

    return user


@router.put("/me", response_model=UserRead)
async def update_me(
        user_update: UserUpdate,
        user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):


    update_data = user_update.dict(exclude_unset=True)
    allowed_fields = ['username']

    for field in allowed_fields:
        if field in update_data:
            setattr(user, field, update_data[field])

    await db.commit()
    await db.refresh(user)
    return user


@router.get("/", response_model=List[UserRead])
async def get_users(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(current_active_user)
):

    if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/join-team/{invite_code}")
async def join_team(
        invite_code: str,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(current_active_user)
):


    result = await db.execute(select(Team).where(Team.invite_code == invite_code))
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(status_code=404, detail="Invalid invite code")


    current_user.member_of_team = team.team_id
    await db.commit()

    return {"message": f"Successfully joined team {team.team_name}"}


@router.post("/leave-team")
async def leave_team(
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(current_active_user)
):

    if not current_user.member_of_team:
        raise HTTPException(status_code=400, detail="Not a member of any team")

    current_user.member_of_team = None
    await db.commit()

    return {"message": "Successfully left the team"}