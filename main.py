"""
Основной скрипт создания и запуска приложения + админка
"""
import os
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin
from app.database.database import (engine,create_db_and_tables)
from app.database.models import RoleEnum
from app.fastapi_users import (fastapi_users,auth_backend,get_user_db,get_user_manager)
from app.schemas import (UserRead,UserCreate,UserUpdate)
from app.admin import (SimpleAuth,UserAdmin,TeamAdmin,TaskAdmin,MeetingAdmin,EvaluationAdmin)
from app.routers import (users,teams,tasks,meetings,evaluations,calendar)
from fastapi_users.exceptions import UserAlreadyExists


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")


admin = None


# TODO вынести в app/fastapi_users
async def create_admin_user():
    """Создание администратора через UserManager"""
    if not all([ADMIN_EMAIL, ADMIN_PASSWORD]):
        print("Admin credentials not provided in .env")
        return
    try:
        async for user_db in get_user_db():
            async for user_manager in get_user_manager(user_db):
                try:
                    existing_user = await user_manager.get_by_email(ADMIN_EMAIL)
                    if existing_user:
                        print(f"Admin user {ADMIN_EMAIL} already exists")
                        if not existing_user.is_superuser or existing_user.role != RoleEnum.admin:
                            update_dict = {
                                "is_superuser": True,
                                "role": RoleEnum.admin,
                                "is_verified": True
                            }
                            await user_manager.user_db.update(existing_user, update_dict)
                            print(f"Updated existing user {ADMIN_EMAIL} to admin")
                        return

                except Exception:
                    pass

                try:
                    user_create = UserCreate(email=ADMIN_EMAIL,password=ADMIN_PASSWORD,username=ADMIN_USERNAME or ADMIN_EMAIL.split('@')[0])

                    admin_user = await user_manager.create(user_create,safe=False)

                    update_dict = {
                        "is_superuser": True,
                        "role": RoleEnum.admin,
                        "is_verified": True
                    }
                    await user_manager.user_db.update(admin_user, update_dict)

                    print(f"Admin user {ADMIN_EMAIL} created successfully")
                    return

                except UserAlreadyExists:
                    print(f"Admin user {ADMIN_EMAIL} already exists")
                    return

    except Exception as e:
        print(f"Error creating admin user: {e}")

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

app = FastAPI()

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

def main():
    """Запуск сервера"""
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)

if __name__ == "__main__":
    main()
