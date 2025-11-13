"""
Основной скрипт создания и запуска приложения + админка
"""
import os
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, Request
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin
from app.database.database import (engine,create_db_and_tables)
from app.fastapi_users import fastapi_users,auth_backend, create_admin_user
from app.schemas import (UserRead,UserCreate,UserUpdate)
from app.admin import (SimpleAuth,UserAdmin,TeamAdmin,TaskAdmin,MeetingAdmin,EvaluationAdmin)
from app.routers import (users,teams,tasks,meetings,evaluations,calendar)


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")


admin = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Основной цикл"""
    global admin

    await create_db_and_tables()

    # Инициализация админки
    admin = Admin(app=application,engine=engine,authentication_backend=SimpleAuth(SECRET_KEY),base_url="/admin")

    admin.add_view(UserAdmin)
    admin.add_view(TeamAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(MeetingAdmin)
    admin.add_view(EvaluationAdmin)

    # Создание администратора через UserManager
    await create_admin_user()

    yield

    await engine.dispose()

app = FastAPI(lifespan=lifespan)

router = APIRouter()

# Middleware
app.add_middleware(SessionMiddleware,secret_key=SECRET_KEY,session_cookie="session")

# Аутентификация fastapi-users
app.include_router(fastapi_users.get_auth_router(auth_backend),prefix="/auth/jwt",tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate),prefix="/auth",tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(),prefix="/auth",tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead),prefix="/auth",tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate),prefix="/users",tags=["users"])

# API роутеры
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(tasks.router)
app.include_router(meetings.router)
app.include_router(evaluations.router)
app.include_router(calendar.router)

# Роутер главной страницы
app.include_router(router)
templates = Jinja2Templates(directory="app/templates")


# TODO убрать куда нибудь в роутеры
@app.get("/")
def root_page(request: Request):
    content = {

    }
    return templates.TemplateResponse("index.html",
                                      {"request": request, **content})



def main():
    """Запуск сервера"""
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)

if __name__ == "__main__":
    main()
