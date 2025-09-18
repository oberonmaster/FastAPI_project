"""
Основной скрипт создания и запуска приложения + админ
"""
import os
import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin
from app.database.database import engine, Base
from app.users import fastapi_users, auth_backend, current_active_user
from app.schemas import UserRead, UserCreate, UserUpdate
from app.database.database import create_db_and_tables
from contextlib import asynccontextmanager

from app.admin import (SimpleAuth,
                       UserAdmin,
                       TeamAdmin,
                       TaskAdmin,
                       MeetingAdmin)

app = FastAPI(title="My FastAPI App")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-secret"))

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"]
)

@asynccontextmanager
async def lifespan(app: FastAPI):

    await create_db_and_tables()
    admin = Admin(app=app,
                  engine=engine,
                  authentication_backend=SimpleAuth(SECRET_KEY),
                  base_url="/admin")
    admin.add_view(UserAdmin)
    admin.add_view(TeamAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(MeetingAdmin)

    # Всё готово — отдаём управление FastAPI (сервер стартует)
    yield

    # --- shutdown ---
    await engine.dispose()


#Admin panel
SECRET_KEY = os.getenv("SECRET_KEY")
admin = Admin(app=app,
              engine=engine,
              authentication_backend=SimpleAuth(SECRET_KEY),
              base_url="/admin")
admin.add_view(UserAdmin)
admin.add_view(TeamAdmin)
admin.add_view(TaskAdmin)
admin.add_view(MeetingAdmin)

def main():
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=8000,
                reload=True)


if __name__ == "__main__":
    main()
