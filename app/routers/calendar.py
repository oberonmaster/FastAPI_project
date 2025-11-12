"""
геттеры календаря
"""
from fastapi import (APIRouter,Depends)
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date, timedelta
from app.database.database import get_async_session
from app.database.models import User
from app.schemas import CalendarEventResponse,DayCalendarResponse
from app.fastapi_users import current_active_user
from app.services.calendar_service import get_events_utility, get_month_utility, get_day_utility


router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events", response_model=CalendarEventResponse)
async def get_calendar_events(start_date: date,end_date: date,db: AsyncSession = Depends(get_async_session),current_user: User = Depends(current_active_user)):
    """Получить события календаря"""
    events = await get_events_utility(db, current_user, start_date, end_date)
    return CalendarEventResponse(events=events)


@router.get("/month/{year}/{month}")
async def get_month_calendar(year: int,month: int,db: AsyncSession = Depends(get_async_session),current_user: User = Depends(current_active_user)):
    """Получить календарь на месяц"""
    return await get_month_utility(year, month, db, current_user)


@router.get("/day/{year}/{month}/{day}", response_model=DayCalendarResponse)
async def get_day_calendar(year: int,month: int,day: int,db: AsyncSession = Depends(get_async_session),current_user: User = Depends(current_active_user)):
    """Получить события дня"""
    result = await get_day_utility(year, month, day, db, current_user)
    return DayCalendarResponse(**result)

@router.get("/upcoming")
async def get_upcoming_events(days: int = 7,db: AsyncSession = Depends(get_async_session),current_user: User = Depends(current_active_user)):
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)
    events = await get_events_utility(db, current_user, start_date.date(), end_date.date())
    events.sort(key=lambda x: x.start)

    return {
        "period": f"Next {days} days",
        "events": events[:10]
    }
