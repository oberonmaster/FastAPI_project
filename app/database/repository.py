"""Репозиторий для работы с базой данных - выносим все запросы сюда"""
from datetime import datetime, date, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models import Task, Meeting, Evaluation, Comment, Team, User


class CalendarRepository:
    """Репозиторий для календаря"""

    @staticmethod
    async def get_user_tasks_by_date_range(
            db: AsyncSession,
            user_id: int,
            start_date: date,
            end_date: date
    ) -> List[Task]:
        """Получить задачи пользователя по диапазону дат"""
        result = await db.execute(
            select(Task).where(
                Task.task_executor == user_id,
                Task.deadline >= start_date,
                Task.deadline <= end_date
            )
        )
        return result.scalars().all()

    @staticmethod
    async def get_user_meetings_by_date_range(
            db: AsyncSession,
            user_id: int,
            start_date: date,
            end_date: date
    ) -> List[Meeting]:
        """Получить встречи пользователя по диапазону дат"""
        result = await db.execute(
            select(Meeting).where(
                Meeting.participants.any(id=user_id),
                Meeting.meeting_date >= start_date,
                Meeting.meeting_date <= end_date
            )
        )
        return result.scalars().all()


class EvaluationRepository:
    """Репозиторий для оценок"""

    @staticmethod
    async def get_user_average_rating(
            db: AsyncSession,
            user_id: int,
            period_days: int
    ) -> dict:
        """Получить средний рейтинг пользователя (исправленная версия)"""
        # Исправляем устаревший метод utcnow()
        start_date = datetime.now() - timedelta(days=period_days)

        result = await db.execute(
            select(Evaluation).join(Evaluation.task).where(
                Task.task_executor == user_id,
                Evaluation.created_at >= start_date
            )
        )
        evaluations = result.scalars().all()

        if not evaluations:
            return {"average_rating": None, "total_evaluations": 0}

        total = sum(eval.evaluation_value for eval in evaluations)
        average = total / len(evaluations)

        return {
            "average_rating": round(average, 2),
            "total_evaluations": len(evaluations),
            "period_days": period_days
        }


class TaskRepository:
    """Репозиторий для задач"""

    @staticmethod
    async def get_tasks_by_filters(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            status: Optional[str] = None,
            team_id: Optional[int] = None,
            user_id: Optional[int] = None
    ) -> List[Task]:
        query = select(Task)

        if status:
            query = query.where(Task.status == status)
        if team_id:
            query = query.where(Task.team_id == team_id)
        if user_id:
            query = query.where(Task.task_executor == user_id)

        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_task_by_id(db: AsyncSession, task_id: int) -> Optional[Task]:
        result = await db.execute(select(Task).where(Task.task_id == task_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_tasks(db: AsyncSession, user_id: int) -> List[Task]:
        result = await db.execute(
            select(Task).where(
                (Task.task_executor == user_id) | (Task.task_checker == user_id)
            )
        )
        return result.scalars().all()


class UserRepository:
    """Репозиторий для пользователей"""

    @staticmethod
    async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


class TeamRepository:
    """Репозиторий для команд"""

    @staticmethod
    async def get_teams(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Team]:
        result = await db.execute(select(Team).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_team_by_id(db: AsyncSession, team_id: int) -> Optional[Team]:
        result = await db.execute(select(Team).where(Team.team_id == team_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_team_by_invite_code(db: AsyncSession, invite_code: str) -> Optional[Team]:
        result = await db.execute(select(Team).where(Team.invite_code == invite_code))
        return result.scalar_one_or_none()


class MeetingRepository:
    """Репозиторий для встреч"""

    @staticmethod
    async def get_meetings_by_filters(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            user_id: Optional[int] = None
    ) -> List[Meeting]:
        query = select(Meeting)

        if start_date:
            query = query.where(Meeting.meeting_date >= start_date)
        if end_date:
            query = query.where(Meeting.meeting_date <= end_date)
        if user_id:
            query = query.where(Meeting.participants.any(id=user_id))

        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_meeting_by_id(db: AsyncSession, meeting_id: int) -> Optional[Meeting]:
        result = await db.execute(select(Meeting).where(Meeting.meeting_id == meeting_id))
        return result.scalar_one_or_none()


class CommentRepository:
    """Репозиторий для комментариев"""

    @staticmethod
    async def get_comments_by_task_id(db: AsyncSession, task_id: int) -> List[Comment]:
        result = await db.execute(select(Comment).where(Comment.task_id == task_id))
        return result.scalars().all()


# Создаем экземпляры репозиториев
calendar_repo = CalendarRepository()
evaluation_repo = EvaluationRepository()
task_repo = TaskRepository()
user_repo = UserRepository()
team_repo = TeamRepository()
meeting_repo = MeetingRepository()
comment_repo = CommentRepository()