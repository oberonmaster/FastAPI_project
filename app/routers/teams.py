"""

"""
# TODO две строки между классами

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import secrets
from app.database.database import get_async_session
from app.database.models import User, RoleEnum
from app.database.repository import team_repo, user_repo
from app.users import current_active_user
from app.schemas import TeamCreate, TeamRead
from app.dependencies import get_team_admin_user


router = APIRouter(prefix="/teams", tags=["teams"])


def generate_invite_code():
    return secrets.token_urlsafe(8)


@router.post("/", response_model=TeamRead)
async def create_team(
        team: TeamCreate,
        current_user: User = Depends(get_team_admin_user),
        db: AsyncSession = Depends(get_async_session)
):
    """создание команды"""
    invite_code = generate_invite_code()
    while True:
        existing_team = await team_repo.get_team_by_invite_code(db, invite_code)
        if not existing_team:
            break
        invite_code = generate_invite_code()

    team_data = {
        "team_name": team.team_name,
        "team_admin": current_user.id,
        "invite_code": invite_code
    }

    db_team = await team_repo.create_team(db, team_data)

    await user_repo.update_user_team(db, current_user.id, db_team.team_id)

    return TeamRead.model_validate(db_team)


@router.get("/", response_model=List[TeamRead])
async def get_teams(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """получение списка комманд"""
    if current_user.role == RoleEnum.admin:
        teams = await team_repo.get_teams(db, skip, limit)
    else:
        if current_user.member_of_team:
            team = await team_repo.get_team_by_id(db, current_user.member_of_team)
            teams = [team] if team else []
        else:
            teams = []

    return [TeamRead.model_validate(team) for team in teams]


@router.get("/{team_id}", response_model=TeamRead)
async def get_team(
        team_id: int,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """ получение команды по id"""
    team = await team_repo.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    if (current_user.role != RoleEnum.admin and
            current_user.member_of_team != team_id and
            current_user.id != team.team_admin):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    return TeamRead.model_validate(team)


@router.put("/{team_id}", response_model=TeamRead)
async def update_team(
        team_id: int,
        team_update: TeamCreate,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """обновление команды"""
    team = await team_repo.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    if current_user.role != RoleEnum.admin and current_user.id != team.team_admin:
        raise HTTPException(
            status_code=403,
            detail="Not team admin"
        )

    team_data = {
        "team_name": team_update.team_name
    }

    updated_team = await team_repo.update_team(db, team_data)
    return TeamRead.model_validate(updated_team)


@router.delete("/{team_id}")
async def delete_team(
        team_id: int,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """удаление команды"""
    team = await team_repo.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    if current_user.role != RoleEnum.admin and current_user.id != team.team_admin:
        raise HTTPException(
            status_code=403,
            detail="Not team admin"
        )

    await team_repo.delete(db, team_id)
    return {"message": "Team deleted successfully"}


@router.post("/{team_id}/generate-invite")
async def generate_new_invite(
        team_id: int,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """генерация нового приглашения"""
    team = await team_repo.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    if current_user.role != RoleEnum.admin and current_user.id != team.team_admin:
        raise HTTPException(
            status_code=403,
            detail="Not team admin"
        )

    invite_code = generate_invite_code()

    while True:
        existing_team = await team_repo.get_team_by_invite_code(db, invite_code)
        if not existing_team or existing_team.team_id == team_id:
            break
        invite_code = generate_invite_code()

    team_data = {
        "invite_code": invite_code
    }
    await team_repo.update_team(db, team_id, team_data)
    return {"invite_code": team.invite_code}


@router.post("/{team_id}/remove-user/{user_id}")
async def remove_user_from_team(
        team_id: int,
        user_id: int,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """исключение пользователя из команды"""
    team = await team_repo.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    if current_user.role != RoleEnum.admin and current_user.id != team.team_admin:
        raise HTTPException(
            status_code=403,
            detail="Not team admin"
        )

    user_to_remove = await team_repo.get_team_by_id(db, user_id)

    if not user_to_remove or user_to_remove.member_of_team != team_id:
        raise HTTPException(
            status_code=404,
            detail="User not found in team"
        )

    await user_repo.update_user_team(db, user_id, None)
    return {"message": f"User {user_to_remove.username} removed from team"}
