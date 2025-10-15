"""Dependencies"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_async_session
from app.database.models import User, Team, RoleEnum
from app.users import current_active_user


async def get_admin_user(current_user: User = Depends(current_active_user)):
    """getting admin user"""
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_manager_user(current_user: User = Depends(current_active_user)):
    """getting manager user"""
    if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required"
        )
    return current_user


async def get_team_admin_user(current_user: User = Depends(current_active_user)):
    """getting team admin user"""
    if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team admin access required"
        )
    return current_user


async def verify_team_member(
        team_id: int,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Verification of team member"""

    if current_user.role in [RoleEnum.admin]:
        return current_user

    team = await db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if current_user.member_of_team != team_id and current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this team"
        )

    return current_user
