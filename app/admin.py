"""Main admin panel"""
import os
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from fastapi_users.password import PasswordHelper
from wtforms import PasswordField
from fastapi import HTTPException
from app.database.models import User, Team, Task, Meeting, Evaluation, Comment


password_helper = PasswordHelper()

""" аутентификация """
class SimpleAuth(AuthenticationBackend):
    """Auth default admin user"""
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


# Регистрируем модели
class UserAdmin(ModelView, model=User):
    """User admin panel"""
    column_list = [
        User.id,
        User.username,
        User.email,
        User.is_active,
        User.is_superuser,
        User.is_verified,
        User.role,
        User.member_of_team,
        User.created_at,
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
        "password",
        User.is_active,
        User.is_superuser,
        User.is_verified,
        User.role,
        User.member_of_team,
    ]

    column_formatters = {
        User.created_at: lambda m, a: (
            m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else None
        )
    }

    async def scaffold_form(self, *args, **kwargs):
        form_class = await super().scaffold_form(*args, **kwargs)
        if not hasattr(form_class, "password"):
            setattr(
                form_class, "password",
                PasswordField(
                    "Password",
                    render_kw={"class": "form-control", "id": "password"}
                )
            )
        return form_class

    async def insert_model(self, request: Request, data: dict):
        pw = None
        if "password" in data:
            pw = data.pop("password")
        if not pw:
            raise HTTPException(
                status_code=400,
                detail="Password is required when creating a user via admin.")
        data["hashed_password"] = password_helper.hash(pw)
        return await super().insert_model(request, data)

    async def update_model(self, request: Request, pk, data: dict):
        if "password" in data:
            pw = data.pop("password")
            if pw:
                data["hashed_password"] = password_helper.hash(pw)
            else:
                data.pop("hashed_password", None)

        return await super().update_model(request, pk, data)


class TeamAdmin(ModelView, model=Team):
    """Team admin panel"""
    column_list = [
        Team.team_id,
        Team.team_name,
        Team.admin,
        Team.members,
        Team.invite_code,
        Team.created_at,
    ]

    column_formatters = {
        Team.created_at: lambda m, a: (
            m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else None
        )
    }


class TaskAdmin(ModelView, model=Task):
    """Task admin panel"""
    column_list = [
        Task.task_id,
        Task.task_name,
        Task.status,
        Task.executor,
        Task.checker,
        Task.team,
        Task.deadline,
        Task.evaluations
    ]

    column_formatters = {
        Task.executor: lambda obj, request: obj.executor.username if obj.executor else "—",
        Task.checker: lambda obj, request: obj.checker.username if obj.checker else "—",
        Task.team: lambda obj, request: obj.team.team_name if obj.team else "—",
        Task.deadline: lambda m, a: (
            m.deadline.strftime("%Y-%m-%d %H:%M:%S") if m.deadline else None
        ),
        Task.evaluations: lambda obj, request: ", ".join(
            f"{ev.evaluation_value} (by {ev.evaluator.username if ev.evaluator else '—'})"
            for ev in (obj.evaluations or [])
        )
    }

    column_searchable_list = [Task.task_name]
    column_sortable_list = [Task.task_id, Task.task_name]


class MeetingAdmin(ModelView, model=Meeting):
    """Meeting admin panel"""
    column_list = [
        Meeting.meeting_id,
        Meeting.meeting_name,
        Meeting.meeting_admin,
        Meeting.meeting_date,
        Meeting.duration_minutes,
    ]

    column_formatters = {
        Meeting.meeting_date: lambda m, a: (
            m.meeting_date.strftime("%Y-%m-%d %H:%M:%S") if m.meeting_date else None
        ),
        Meeting.admin: lambda obj, request: obj.admin.username if obj.admin else "—"
    }


class EvaluationAdmin(ModelView, model=Evaluation):
    """Evaluation admin panel"""
    column_list = [
        Evaluation.evaluation_id,
        Evaluation.evaluation_value,
        Evaluation.task,
        Evaluation.evaluator,
        Evaluation.created_at
    ]

    column_formatters = {
        Evaluation.task: lambda obj, request: obj.task.task_name if obj.task else "—",
        Evaluation.evaluator: lambda obj, request: obj.evaluator.username if obj.evaluator else "—",
        Evaluation.created_at: lambda m, a: (
            m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else None
        )
    }

    column_searchable_list = [Evaluation.evaluation_value]
    column_sortable_list = [
        Evaluation.evaluation_id,
        Evaluation.evaluation_value,
        Evaluation.created_at
    ]


class CommentAdmin(ModelView, model=Comment):
    """Comment admin panel"""
    column_list = [
        Comment.comment_id,
        Comment.content,
        Comment.task,
        Comment.author,
        Comment.created_at
    ]

    column_formatters = {
        Comment.task: lambda obj, request: obj.task.task_name if obj.task else "—",
        Comment.author: lambda obj, request: obj.author.username if obj.author else "—",
        Comment.created_at: lambda m, a: (
            m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else None
        )
    }
