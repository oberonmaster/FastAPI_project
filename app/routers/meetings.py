"""роутеры для встреч"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from app.database.database import get_async_session
from app.database.models import User, RoleEnum
from app.fastapi_users import current_active_user
from app.schemas import MeetingCreate, MeetingRead
from app.database.repository import meeting_repo, user_repo


router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/", response_model=MeetingRead)
async def create_meeting(
        meeting: MeetingCreate,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """создание встречи"""
    if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    # проверка участников
    participants = []
    for user_id in meeting.participant_ids:
        user = await user_repo.get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} not found"
            )

        participants.append(user)

    # проверка конфликтующих встреч
    conflict_meetings = await meeting_repo.check_meeting_conflicts(
        db,
        meeting.participant_ids,
        meeting.meeting_date,
        meeting.duration_minutes or 60
    )

    if conflict_meetings:
        conflict_info = []

        for conflict in conflict_meetings:
            for user in conflict.participants:
                if user.id in meeting.participant_ids:
                    conflict_info.append(f"User {user.username} has conflict meeting: {conflict.meeting_name}")
                    break
        raise HTTPException(
            status_code=400,
            detail="; ".join(conflict_info)
        )

    # добавление организатора в список участников
    creator_in_list = any(user.id == current_user.id for user in participants)
    if not creator_in_list:
        creator = await user_repo.get_user_by_id(db, current_user.id)
        if creator:
            participants.append(creator)

    # создание встречи
    meeting_data = {
        "meeting_name": meeting.meeting_name,
        "meeting_description": meeting.meeting_description,
        "meeting_date": meeting.meeting_date,
        "duration_minutes": meeting.duration_minutes or 60,
        "meeting_admin": current_user.id,
        "participants": participants
    }

    db_meeting = await meeting_repo.create_meeting(db, meeting_data)
    return MeetingRead.model_validate(db_meeting)

@router.get("/", response_model=List[MeetingRead])
async def get_meetings(
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """получение информации о встрече"""
    if current_user.role in [RoleEnum.admin]:
        meetings = await meeting_repo.get_meetings_by_filters(db, skip, limit, start_date, end_date)
    else:
        meetings = await meeting_repo.get_meetings_by_filters(db, skip, limit, start_date, end_date, current_user.id)

    return [MeetingRead.model_validate(meeting) for meeting in meetings]


@router.get("/my-meetings", response_model=List[MeetingRead])
async def get_my_meetings(
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Получить встречи текущего пользователя"""
    meetings = await meeting_repo.get_user_meetings(db, current_user.id)
    return [MeetingRead.model_validate(meeting) for meeting in meetings]


@router.get("/{meeting_id}", response_model=MeetingRead)
async def get_meeting(
        meeting_id: int,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """получение встречи по id"""
    meeting = await meeting_repo.get_meeting_by_id(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    if (current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager] and
            current_user not in meeting.participants):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    return MeetingRead.model_validate(meeting)


@router.put("/{meeting_id}", response_model=MeetingRead)
async def update_meeting(
        meeting_id: int,
        meeting_update: MeetingCreate,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """ обновление встречи """
    meeting = await meeting_repo.get_meeting_by_id(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    if meeting.meeting_admin != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=403,
            detail="Not meeting admin"
        )

    # проверка участников
    participants = []
    for user_id in meeting_update.participant_ids:
        user = await user_repo.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} not found"
            )
        participants.append(user)

    # проверка конфликтов
    conflict_meetings = await meeting_repo.check_meeting_conflicts(
        db,
        meeting_update.participant_ids,
        meeting_update.meeting_date,
        meeting_update.duration_minutes or 60,
        meeting_id
    )

    if conflict_meetings:
        conflict_info = []
        for conflict in conflict_meetings:
            for user in conflict.participants:
                if user.id in meeting_update.participant_ids:
                    conflict_info.append(f"User {user.username} has conflict meeting: {conflict.meeting_name}")
                    break
        raise HTTPException(
            status_code=400,
            detail="; ".join(conflict_info)
        )

    # обновление встречи
    meeting_data = {
        "meeting_name": meeting_update.meeting_name,
        "meeting_description": meeting_update.meeting_description,
        "meeting_date": meeting_update.meeting_date,
        "duration_minutes": meeting_update.duration_minutes or 60,
        "participants": participants
    }

    updated_meeting = await meeting_repo.update_meeting(db, meeting_id, meeting_data)
    return MeetingRead.model_validate(updated_meeting)


@router.delete("/{meeting_id}")
async def delete_meeting(
        meeting_id: int,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """удаление встречи"""
    meeting = await meeting_repo.get_meeting_by_id(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    if meeting.meeting_admin != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=403,
            detail="Not meeting admin"
        )

    await meeting_repo.delete_meeting(db, meeting_id)
    return {"message": "Meeting deleted successfully"}


@router.post("/{meeting_id}/cancel")
async def cancel_meeting(
        meeting_id: int,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """отмена встерчи"""
    meeting = await meeting_repo.get_meeting_by_id(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    if meeting.meeting_admin != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=403,
            detail="Not meeting admin"
        )

    await meeting_repo.delete_meeting(db, meeting_id)
    return {"message": "Meeting cancelled successfully"}