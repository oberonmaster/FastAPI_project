"""
Основной скрипт создания и запуска приложения + админ
"""
import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin
from app.database.database import engine, create_db_and_tables, async_session_maker
from app.database.models import User
from app.users import fastapi_users, auth_backend
from app.schemas import UserRead, UserCreate, UserUpdate
from app.admin import SimpleAuth, UserAdmin, TeamAdmin, TaskAdmin, MeetingAdmin
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi_users.password import PasswordHelper


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")

password_helper = PasswordHelper()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()

    admin = Admin(app=app, engine=engine, authentication_backend=SimpleAuth(SECRET_KEY), base_url="/admin")
    admin.add_view(UserAdmin)
    admin.add_view(TeamAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(MeetingAdmin)

    if ADMIN_EMAIL and ADMIN_PASSWORD:
        async with async_session_maker() as session:
            user_db = SQLAlchemyUserDatabase(session, User)

            existing = await user_db.get_by_email(ADMIN_EMAIL)
            if not existing:
                hashed = password_helper.hash(ADMIN_PASSWORD)
                user_dict = {
                    "email": ADMIN_EMAIL,
                    "hashed_password": hashed,
                    "username": ADMIN_USERNAME,
                    "is_active": True,
                    "is_verified": True,
                    "is_superuser": True,
                }
                await user_db.create(user_dict)
                print(f"[startup] Admin user {ADMIN_EMAIL} created")
            else:
                print(f"[startup] Admin user {ADMIN_EMAIL} already exists")

    yield

    await engine.dispose()


app = FastAPI(title="My FastAPI App", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])


def main():
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=8000,
                reload=True)


if __name__ == "__main__":
    main()
