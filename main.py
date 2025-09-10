"""
Основной скрипт создания и запуска приложения + админ
"""
import os
import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from app.database.database import engine, Base
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from app.database.models import User, Team, Task, Meeting, Evaluation

app = FastAPI(title="My FastAPI App")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-secret"))

Base.metadata.create_all(bind=engine)

# TODO вынести в отдельный модуль
""" аутентификация """
class SimpleAuth(AuthenticationBackend):
    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("admin_user"))

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if username == os.getenv("ADMIN_USERNAME") and password == os.getenv("ADMIN_PASSWORD"):
            request.session["admin_user"] = username
            return True
        return False

    async def logout(self, request: Request) -> None:
        request.session.pop("admin_user", None)


# TODO вынести в отдельный модуль
""" Инициализация админа """
SECRET_KEY = os.getenv("SECRET_KEY")
admin = Admin(app=app,
              engine=engine,
              authentication_backend=SimpleAuth(SECRET_KEY),
              base_url="/admin")

# TODO вынести в отдельный модуль
"""Регистрируем модели"""
class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username]

class TeamAdmin(ModelView, model=Team):
    column_list = [Team.id, Team.team_name]


admin.add_view(UserAdmin)
admin.add_view(TeamAdmin)
# admin.add_view(TaskAdmin) ...

def main():
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=8000,
                reload=True)


if __name__ == "__main__":
    main()
