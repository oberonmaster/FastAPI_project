import os
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from app.database.models import User, Team, Task, Meeting
from starlette.requests import Request
from markupsafe import Markup
from fastapi_users.password import PasswordHelper


password_helper = PasswordHelper()

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


"""Регистрируем модели"""
class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.username,
        User.email,
        User.is_active,
        User.is_superuser,
        User.is_verified,
        User.created_at,
        User.member_of_team,
    ]

    column_searchable_list = [
        User.username,
        User.email
    ]

    column_sortable_list = [
        User.id,
        User.username
    ]

    form_columns = [
        User.username,
        User.email,
        User.hashed_password,
        User.is_active,
        User.is_superuser,
        User.is_verified,
        User.member_of_team,
    ]


class TeamAdmin(ModelView, model=Team):
    column_list = [
        Team.team_id,
        Team.team_name,
        Team.admin,
        Team.members,
    ]


class TaskAdmin(ModelView, model=Task):
    column_list = [
        Task.task_id,
        Task.task_name,
        Task.task_executor,
        Task.task_checker,
        Task.evaluations
    ]


class MeetingAdmin(ModelView, model=Meeting):
    column_list = [
        Meeting.meeting_id,
        Meeting.meeting_name,
        Meeting.meeting_admin,
        Meeting.meeting_date,
    ]