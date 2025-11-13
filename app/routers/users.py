"""

"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.database import get_async_session
from app.database.models import User, RoleEnum
from app.database.repository import user_repo, team_repo
from app.fastapi_users import current_active_user
from app.schemas import UserRead, UserUpdate


router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=List[UserRead])
async def get_users(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(current_active_user)
):
    """ получение пользователей"""
    if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    users = await user_repo.get_users(db, skip, limit)
    return [UserRead.model_validate(user) for user in users]


@router.post("/join-team/{invite_code}")
async def join_team(
        invite_code: str,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(current_active_user)
):
    """присоединить к группе"""
    team = await team_repo.get_team_by_invite_code(db, invite_code)
    if not team:
        raise HTTPException(
            status_code=404,
            detail="Invalid invite code"
        )

    await user_repo.update_user_team(db, current_user.id, team.team_id)
    return {"message": f"Successfully joined team {team.team_name}"}


@router.post("/leave-team")
async def leave_team(
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(current_active_user)
):
    """покинуть группу"""
    if not current_user.member_of_team:
        raise HTTPException(
            status_code=400,
            detail="Not a member of any team"
        )
    await user_repo.update_user_team(db, current_user.id, None)
    return {"message": "Successfully left the team"}
