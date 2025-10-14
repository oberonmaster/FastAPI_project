from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from typing import List
import secrets
from app.database.database import async_session_maker
from app.database.models import Team, User, RoleEnum
from app.users import current_active_user
from app.schemas import TeamCreate, TeamRead
from app.dependencies import get_team_admin_user


router = APIRouter(prefix="/teams", tags=["teams"])


def generate_invite_code():
    return secrets.token_urlsafe(8)


@router.post("/", response_model=TeamRead)
async def create_team(
        team: TeamCreate,
        current_user: User = Depends(get_team_admin_user)
):
    async with async_session_maker() as session:
        invite_code = generate_invite_code()


        while True:
            result = await session.execute(select(Team).where(Team.invite_code == invite_code))
            if not result.scalar_one_or_none():
                break
            invite_code = generate_invite_code()

        db_team = Team(
            team_name=team.team_name,
            team_admin=current_user.id,
            invite_code=invite_code
        )
        session.add(db_team)
        await session.commit()
        await session.refresh(db_team)

        current_user.member_of_team = db_team.team_id
        await session.commit()

        return db_team


@router.get("/", response_model=List[TeamRead])
async def get_teams(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:

        if current_user.role == RoleEnum.admin:
            result = await session.execute(select(Team).offset(skip).limit(limit))
        else:
            result = await session.execute(
                select(Team).where(Team.team_id == current_user.member_of_team)
                .offset(skip).limit(limit)
            )
        return result.scalars().all()


@router.get("/{team_id}", response_model=TeamRead)
async def get_team(
        team_id: int,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        team = await session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if (current_user.role != RoleEnum.admin and
                current_user.member_of_team != team_id and
                current_user.id != team.team_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        return team


@router.put("/{team_id}", response_model=TeamRead)
async def update_team(
        team_id: int,
        team_update: TeamCreate,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        team = await session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if current_user.role != RoleEnum.admin and current_user.id != team.team_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not team admin"
            )

        team.team_name = team_update.team_name
        await session.commit()
        await session.refresh(team)
        return team


@router.delete("/{team_id}")
async def delete_team(
        team_id: int,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        team = await session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if current_user.role != RoleEnum.admin and current_user.id != team.team_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not team admin"
            )

        await session.delete(team)
        await session.commit()
        return {"message": "Team deleted successfully"}


@router.post("/{team_id}/generate-invite")
async def generate_new_invite(
        team_id: int,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        team = await session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if current_user.role != RoleEnum.admin and current_user.id != team.team_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not team admin"
            )


        team.invite_code = generate_invite_code()
        await session.commit()
        await session.refresh(team)

        return {"invite_code": team.invite_code}


@router.post("/{team_id}/remove-user/{user_id}")
async def remove_user_from_team(
        team_id: int,
        user_id: int,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        team = await session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if current_user.role != RoleEnum.admin and current_user.id != team.team_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not team admin"
            )

        user_to_remove = await session.get(User, user_id)
        if not user_to_remove or user_to_remove.member_of_team != team_id:
            raise HTTPException(status_code=404, detail="User not found in team")

        user_to_remove.member_of_team = None
        await session.commit()

        return {"message": f"User {user_to_remove.username} removed from team"}