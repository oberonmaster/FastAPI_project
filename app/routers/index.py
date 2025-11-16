from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_async_session
from app.database.repository import user_repo, task_repo, meeting_repo
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

index_router = APIRouter()

@index_router.get("/")
async def root_page(request: Request, db: AsyncSession = Depends(get_async_session)):
    users = await user_repo.get_users(db, skip=0, limit=10)
    tasks = await task_repo.get_tasks_by_filters(db, skip=0, limit=10)
    meetings = await meeting_repo.get_meetings_by_filters(db, skip=0, limit=100)

    context = {
        "request": request,
        "users": users,
        "tasks": tasks,
        "meetings": meetings
    }

    return templates.TemplateResponse(
        "index.html",
        context
    )
