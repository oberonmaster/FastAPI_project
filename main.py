"""
Основной скрипт создания и запуска приложения + админ
"""
import os
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin
from sqlalchemy import select
from fastapi_users.password import PasswordHelper
from app.database.database import (engine,
                                   create_db_and_tables,
                                   async_session_maker)
from app.database.models import User
from app.users import (fastapi_users,
                       auth_backend)
from app.schemas import (UserRead,
                         UserCreate,
                         UserUpdate)
from app.admin import (SimpleAuth,
                       UserAdmin,
                       TeamAdmin,
                       TaskAdmin,
                       MeetingAdmin,
                       EvaluationAdmin)
from app.routers import (users,
                         teams,
                         tasks,
                         meetings,
                         evaluations,
                         calendar)


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Основной цикл"""
    await create_db_and_tables()

    admin = Admin(app=application,
                  engine=engine,
                  authentication_backend=SimpleAuth(SECRET_KEY),
                  base_url="/admin")
    admin.add_view(UserAdmin)
    admin.add_view(TeamAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(MeetingAdmin)
    admin.add_view(EvaluationAdmin)

    if ADMIN_EMAIL and ADMIN_PASSWORD:
        async with async_session_maker() as session:
            result = await session.execute(select(User).
                                           where(User.email == ADMIN_EMAIL))
            existing = result.scalar_one_or_none()

            if not existing:
                password_helper = PasswordHelper()
                hashed_password = password_helper.hash(ADMIN_PASSWORD)
                admin_user = User(email=ADMIN_EMAIL,
                                  hashed_password=hashed_password,
                                  username=ADMIN_USERNAME,
                                  is_active=True,
                                  is_verified=True,
                                  is_superuser=True,
                                  role="admin")
                session.add(admin_user)

                await session.commit()
                print(f"[startup] Admin user {ADMIN_EMAIL} created")

            else:
                print(f"[startup] Admin user {ADMIN_EMAIL} already exists")
    yield

    await engine.dispose()

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware,
                   secret_key=SECRET_KEY)

# fastapi-users
app.include_router(fastapi_users.get_auth_router(auth_backend),
                   prefix="/auth/jwt",
                   tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate),
                   prefix="/auth",
                   tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(),
                   prefix="/auth",
                   tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead),
                   prefix="/auth",
                   tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate),
                   prefix="/users",
                   tags=["users"])

# API роутеры
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(tasks.router)
app.include_router(meetings.router)
app.include_router(evaluations.router)
app.include_router(calendar.router)


def main():
    """запуск сервера"""
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=8000,
                reload=True,)


if __name__ == "__main__":
    main()
