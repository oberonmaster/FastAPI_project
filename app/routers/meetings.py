from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from typing import List, Optional
from datetime import datetime, timedelta
from app.database.database import async_session_maker
from app.database.models import Meeting, User, RoleEnum
from app.users import current_active_user
from app.schemas import MeetingCreate, MeetingRead


router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/", response_model=MeetingRead)
async def create_meeting(
        meeting: MeetingCreate,
        current_user: User = Depends(current_active_user)
):
    if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    async with async_session_maker() as session:
        meeting_end = meeting.meeting_date + timedelta(minutes=meeting.duration_minutes or 60)

        for user_id in meeting.participant_ids:
            user = await session.get(User, user_id)
            if not user:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")

            existing_meetings_result = await session.execute(
                select(Meeting).join(Meeting.participants).where(
                    User.id == user_id
                )
            )
            existing_meetings = existing_meetings_result.scalars().all()

            for existing_meeting in existing_meetings:
                existing_meeting_end = existing_meeting.meeting_date + timedelta(
                    minutes=existing_meeting.duration_minutes)

                if (meeting.meeting_date < existing_meeting_end and
                        meeting_end > existing_meeting.meeting_date):
                    raise HTTPException(
                        status_code=400,
                        detail=f"User {user.username} has a conflicting meeting: {existing_meeting.meeting_name}"
                    )


        participants = []
        for user_id in meeting.participant_ids:
            user = await session.get(User, user_id)
            if user:
                participants.append(user)


        creator_in_list = any(user.id == current_user.id for user in participants)
        if not creator_in_list:
            participants.append(current_user)

        db_meeting = Meeting(
            meeting_name=meeting.meeting_name,
            meeting_description=meeting.meeting_description,
            meeting_date=meeting.meeting_date,
            duration_minutes=meeting.duration_minutes or 60,
            meeting_admin=current_user.id,
            participants=participants
        )
        session.add(db_meeting)
        await session.commit()
        await session.refresh(db_meeting)
        return db_meeting


@router.get("/", response_model=List[MeetingRead])
async def get_meetings(
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:

        query = select(Meeting)


        if start_date:
            query = query.where(Meeting.meeting_date >= start_date)
        if end_date:
            query = query.where(Meeting.meeting_date <= end_date)

        if current_user.role in [RoleEnum.admin]:
            pass
        else:
            query = query.where(Meeting.participants.any(id=current_user.id))

        result = await session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()


@router.get("/my-meetings", response_model=List[MeetingRead])
async def get_my_meetings(
        current_user: User = Depends(current_active_user)
):
    """Получить встречи текущего пользователя"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Meeting).where(Meeting.participants.any(id=current_user.id))
            .order_by(Meeting.meeting_date)
        )
        return result.scalars().all()


@router.get("/{meeting_id}", response_model=MeetingRead)
async def get_meeting(
        meeting_id: int,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        meeting = await session.get(Meeting, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")


        if (current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager] and
                current_user not in meeting.participants):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        return meeting


@router.put("/{meeting_id}", response_model=MeetingRead)
async def update_meeting(
        meeting_id: int,
        meeting_update: MeetingCreate,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        meeting = await session.get(Meeting, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        if meeting.meeting_admin != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not meeting admin"
            )


        meeting_end = meeting_update.meeting_date + timedelta(minutes=meeting_update.duration_minutes or 60)

        for user_id in meeting_update.participant_ids:
            user = await session.get(User, user_id)
            if not user:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")


            existing_meetings_result = await session.execute(
                select(Meeting).join(Meeting.participants).where(
                    User.id == user_id,
                    Meeting.meeting_id != meeting_id

                )
            )
            existing_meetings = existing_meetings_result.scalars().all()

            for existing_meeting in existing_meetings:
                existing_meeting_end = existing_meeting.meeting_date + timedelta(
                    minutes=existing_meeting.duration_minutes)

                if (meeting_update.meeting_date < existing_meeting_end and
                        meeting_end > existing_meeting.meeting_date):
                    raise HTTPException(
                        status_code=400,
                        detail=f"User {user.username} has a conflicting meeting: {existing_meeting.meeting_name}"
                    )


        participants = []
        for user_id in meeting_update.participant_ids:
            user = await session.get(User, user_id)
            if user:
                participants.append(user)


        meeting.meeting_name = meeting_update.meeting_name
        meeting.meeting_description = meeting_update.meeting_description
        meeting.meeting_date = meeting_update.meeting_date
        meeting.duration_minutes = meeting_update.duration_minutes or 60
        meeting.participants = participants

        await session.commit()
        await session.refresh(meeting)
        return meeting


@router.delete("/{meeting_id}")
async def delete_meeting(
        meeting_id: int,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        meeting = await session.get(Meeting, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        if meeting.meeting_admin != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not meeting admin"
            )

        await session.delete(meeting)
        await session.commit()
        return {"message": "Meeting deleted successfully"}


@router.post("/{meeting_id}/cancel")
async def cancel_meeting(
        meeting_id: int,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        meeting = await session.get(Meeting, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        if meeting.meeting_admin != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not meeting admin"
            )

        await session.delete(meeting)
        await session.commit()
        return {"message": "Meeting cancelled successfully"}