from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_async_session
from app.database.repository import user_repo, task_repo, meeting_repo, team_repo
from fastapi.templating import Jinja2Templates
from datetime import datetime, date
from calendar import monthrange, month_name
from typing import List, Dict, Any

templates = Jinja2Templates(directory="app/templates")

index_router = APIRouter()


def generate_calendar_weeks(year: int, month: int, meeting_dates: set, meeting_counts: dict, current_day: int) -> List[
    List[Dict[str, Any]]]:
    """Генерирует данные для отображения календаря"""
    first_day = date(year, month, 1)
    days_in_month = monthrange(year, month)[1]
    first_weekday = first_day.weekday()
    weeks = []
    week = []
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    prev_month_days = monthrange(prev_year, prev_month)[1]

    for i in range(first_weekday):
        day_number = prev_month_days - first_weekday + i + 1
        week.append({
            'day': day_number,
            'month': prev_month,
            'has_meeting': False,
            'is_today': False
        })
    for day in range(1, days_in_month + 1):
        current_date = date(year, month, day)
        has_meeting = current_date in meeting_dates
        meeting_count = meeting_counts.get(current_date, 0)
        week.append({
            'day': day,
            'month': month,
            'has_meeting': has_meeting,
            'meeting_count': meeting_count,
            'is_today': (day == current_day)
        })

        if len(week) == 7:
            weeks.append(week)
            week = []

    next_month = month + 1 if month < 12 else 1
    next_day = 1

    while len(week) < 7:
        week.append({
            'day': next_day,
            'month': next_month,
            'has_meeting': False,
            'is_today': False
        })
        next_day += 1

    if week:
        weeks.append(week)

    return weeks


@index_router.get("/")
async def root_page(
        request: Request,
        db: AsyncSession = Depends(get_async_session),
):
    # информация из базы
    users = await user_repo.get_users(db, skip=0, limit=10)
    teams = await team_repo.get_teams(db, skip=0, limit=10)
    tasks = await task_repo.get_tasks_by_filters(db, skip=0, limit=10)
    meetings = await meeting_repo.get_meetings_by_filters(db, skip=0, limit=10)

    # текущие значения
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    current_day = today.day

    # порядок отображения
    first_day = date(current_year, current_month, 1)
    _, last_day = monthrange(current_year, current_month)
    last_date = date(current_year, current_month, last_day)

    # отображение количества встреч
    meeting_dates = set()
    meeting_counts = {}
    for meeting in meetings:
        if meeting.meeting_date:
            meeting_date = meeting.meeting_date.date()
            if first_day <= meeting_date <= last_date:
                meeting_dates.add(meeting_date)
                meeting_counts[meeting_date] = meeting_counts.get(meeting_date, 0) + 1

    calendar_weeks = generate_calendar_weeks(
        current_year, current_month, meeting_dates, meeting_counts, current_day
    )

    context = {
        "request": request,
        "users": users,
        "tasks": tasks,
        "teams": teams,
        "meetings": meetings,
        "calendar_weeks": calendar_weeks,
        "current_year": current_year,
        "current_month": current_month,
        "current_month_name": month_name[current_month],
    }

    return templates.TemplateResponse("index.html", context)
