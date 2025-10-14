from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict
from datetime import datetime, date, timedelta
from calendar import monthrange
from app.database.database import get_async_session
from app.database.models import Task, Meeting, User
from app.users import current_active_user


router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events")
async def get_calendar_events(
        start_date: date,
        end_date: date,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(current_active_user)
):

    events = []


    tasks_result = await db.execute(
        select(Task).where(
            Task.task_executor == current_user.id,
            Task.deadline >= start_date,
            Task.deadline <= end_date
        )
    )
    tasks = tasks_result.scalars().all()

    for task in tasks:
        events.append({
            "id": f"task_{task.task_id}",
            "title": f"{task.task_name}",
            "start": task.deadline.isoformat() if task.deadline else None,
            "type": "task",
            "status": task.status,
            "description": task.task_description
        })


    meetings_result = await db.execute(
        select(Meeting).where(
            Meeting.participants.any(id=current_user.id),
            Meeting.meeting_date >= start_date,
            Meeting.meeting_date <= end_date
        )
    )
    meetings = meetings_result.scalars().all()

    for meeting in meetings:
        end_time = meeting.meeting_date + timedelta(minutes=meeting.duration_minutes)
        events.append({
            "id": f"meeting_{meeting.meeting_id}",
            "title": f"{meeting.meeting_name}",
            "start": meeting.meeting_date.isoformat(),
            "end": end_time.isoformat(),
            "type": "meeting",
            "description": meeting.meeting_description
        })

    return events


@router.get("/month/{year}/{month}")
async def get_month_calendar(
        year: int,
        month: int,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(current_active_user)
):


    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)


    events = await get_calendar_events(start_date, end_date, db, current_user)


    events_by_day: Dict[date, List[Dict]] = {}
    for event in events:
        event_date = datetime.fromisoformat(event["start"].replace('Z', '+00:00')).date()
        if event_date not in events_by_day:
            events_by_day[event_date] = []
        events_by_day[event_date].append(event)


    calendar_text = f"Calendar for {year}-{month:02d}\n"
    calendar_text += "=" * 30 + "\n"

    current_day = start_date
    while current_day <= end_date:
        day_events = events_by_day.get(current_day, [])
        calendar_text += f"\n{current_day.strftime('%Y-%m-%d %A')}:\n"

        if not day_events:
            calendar_text += "  No events\n"
        else:
            for event in day_events:
                event_type = "📝" if event["type"] == "task" else "👥"
                calendar_text += f"  {event_type} {event['title']}\n"

        current_day += timedelta(days=1)

    return {"calendar": calendar_text.strip()}


@router.get("/day/{year}/{month}/{day}")
async def get_day_calendar(
        year: int,
        month: int,
        day: int,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(current_active_user)
):

    target_date = date(year, month, day)
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())

    events = []


    tasks_result = await db.execute(
        select(Task).where(
            Task.task_executor == current_user.id,
            Task.deadline >= start_datetime,
            Task.deadline <= end_datetime
        )
    )
    tasks = tasks_result.scalars().all()

    for task in tasks:
        events.append({
            "type": "task",
            "id": task.task_id,
            "title": task.task_name,
            "time": task.deadline.strftime("%H:%M") if task.deadline else "All day",
            "status": task.status,
            "description": task.task_description
        })


    meetings_result = await db.execute(
        select(Meeting).where(
            Meeting.participants.any(id=current_user.id),
            Meeting.meeting_date >= start_datetime,
            Meeting.meeting_date <= end_datetime
        ).order_by(Meeting.meeting_date)
    )
    meetings = meetings_result.scalars().all()

    for meeting in meetings:
        events.append({
            "type": "meeting",
            "id": meeting.meeting_id,
            "title": meeting.meeting_name,
            "time": meeting.meeting_date.strftime("%H:%M"),
            "duration": f"{meeting.duration_minutes}min",
            "description": meeting.meeting_description
        })


    events.sort(key=lambda x: x.get('time', ''))

    return {
        "date": target_date.isoformat(),
        "events": events
    }


@router.get("/upcoming")
async def get_upcoming_events(
        days: int = 7,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(current_active_user)
):


    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)

    events = await get_calendar_events(
        start_date.date(),
        end_date.date(),
        db,
        current_user
    )


    events.sort(key=lambda x: x["start"])

    return {
        "period": f"Next {days} days",
        "events": events[:10]
    }