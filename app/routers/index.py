from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_async_session
from app.database.repository import user_repo, task_repo, meeting_repo, team_repo
from fastapi.templating import Jinja2Templates
# from app.services.calendar_service import get_upcoming_events_utility
from app.database.models import User

templates = Jinja2Templates(directory="app/templates")

index_router = APIRouter()


@index_router.get("/")
async def root_page(
        request: Request,
        db: AsyncSession = Depends(get_async_session),
        # current_user: User = Depends(current_user)
):
    users = await user_repo.get_users(db, skip=0, limit=10)
    teams = await team_repo.get_teams(db, skip=0, limit=10)
    tasks = await task_repo.get_tasks_by_filters(db, skip=0, limit=10)
    meetings = await meeting_repo.get_meetings_by_filters(db, skip=0, limit=10)
    # upcoming_events = await get_upcoming_events_utility(db, current_user)

    context = {
        "request": request,
        # "current_user": current_user,
        "users": users,
        "tasks": tasks,
        "teams": teams,
        "meetings": meetings,
        # "upcoming_events": upcoming_events,
    }

    return templates.TemplateResponse("index.html", context)

