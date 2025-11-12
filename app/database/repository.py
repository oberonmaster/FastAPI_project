"""Репозиторий для работы с базой данных"""
from datetime import datetime, date, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models import Task, Meeting, Evaluation, Comment, Team, User
from app.services.database_error_handler import db_error_handler


class CalendarRepository:
    """Репозиторий календаря"""
    @staticmethod
    async def get_user_tasks_by_date_range(db: AsyncSession,user_id: int,start_date: date,end_date: date) -> List[Task]:
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
    async def get_user_meetings_by_date_range(db: AsyncSession,user_id: int,start_date: date,end_date: date) -> List[Meeting]:
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
    async def get_user_average_rating(db: AsyncSession,user_id: int,period_days: int) -> dict:
        """Получить средний рейтинг пользователя (исправленная версия)"""
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

    @staticmethod
    async def get_evaluations_by_filters(db: AsyncSession,skip: int = 0,limit: int = 100,task_id: Optional[int] = None,user_id: Optional[int] = None) -> List[Evaluation]:
        """Получение оценки по фильтрам"""
        query = select(Evaluation)

        if task_id:
            query = query.where(Evaluation.task_id == task_id)
        if user_id:
            query = query.where(Evaluation.evaluator_id == user_id)

        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_evaluation_by_id(
            db: AsyncSession,
            evaluation_id: int
    ) -> Optional[Evaluation]:
        """Получение оценки по ее id"""
        result = await db.execute(select(Evaluation).where(Evaluation.evaluation_id == evaluation_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_evaluations(db: AsyncSession,user_id: int) -> List[Evaluation]:
        """Получение оценок пользователя"""
        result = await db.execute(select(Evaluation).join(Evaluation.task).where(Task.task_executor == user_id).order_by(Evaluation.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def check_duplicate_evaluations(db: AsyncSession,task_id: int,evaluator_id: int) -> bool:
        """проверка дублей"""
        result = await db.execute(select(Evaluation).where(Evaluation.task_id == task_id,Evaluation.evaluator_id == evaluator_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_evaluation(db: AsyncSession, evaluation_data: dict) -> Optional[Evaluation]:
        """Создать оценку"""
        return await db_error_handler.create_operation(db, Evaluation, evaluation_data)

    @staticmethod
    async def update_evaluation(db: AsyncSession, evaluation_id: int, evaluation_data: dict) -> Optional[Evaluation]:
        """Обновить оценку"""
        return await db_error_handler.update_operation(db, EvaluationRepository.get_evaluation_by_id, evaluation_id, evaluation_data)

    @staticmethod
    async def delete_evaluation(db: AsyncSession, evaluation_id: int) -> bool:
        """Удалить оценку"""
        return await db_error_handler.delete_operation(db, EvaluationRepository.get_evaluation_by_id, evaluation_id)


class TaskRepository:
    """Репозиторий для задач"""
    @staticmethod
    async def get_tasks_by_filters(db: AsyncSession,skip: int = 0,limit: int = 100,status: Optional[str] = None,team_id: Optional[int] = None,user_id: Optional[int] = None) -> List[Task]:
        """получение задачи по фильтру"""
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
    async def get_task_by_id(db: AsyncSession,task_id: int) -> Optional[Task]:
        """Получение задачи по id"""
        result = await db.execute(select(Task).where(Task.task_id == task_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_tasks(db: AsyncSession,user_id: int) -> List[Task]:
        """Поллучение задачи пользователя"""
        result = await db.execute(
            select(Task).where(
                (Task.task_executor == user_id) | (Task.task_checker == user_id)
            )
        )
        return result.scalars().all()

    @staticmethod
    async def creaate_task(db: AsyncSession,task_data: dict) -> Task:
        """Создание новой задачи"""
        return await db_error_handler.create_operation(db, Task, task_data)

    @staticmethod
    async def update_task(db: AsyncSession, task_id: int, task_data: dict) -> Optional[Task]:
        """Обновить задачу"""
        return await db_error_handler.update_operation(db,TaskRepository.get_task_by_id,task_id,task_data)

    @staticmethod
    async def update_task_status(db: AsyncSession,task_id: int,status: str) -> Optional[Task]:
        """обновление статуса выполнения задачи"""
        return await db_error_handler.update_operation(db,TaskRepository.get_task_by_id,task_id,{"status": status})

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: int) -> bool:
        """Удалить задачу"""
        return await db_error_handler.delete_operation(db,TaskRepository.get_task_by_id,task_id)


class UserRepository:
    """Репозиторий для пользователей"""
    @staticmethod
    async def get_users(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100
    ) -> List[User]:
        """получение данных пользователя"""
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_user_by_id(
            db: AsyncSession,
            user_id: int
    ) -> Optional[User]:
        """получения данных пользователя по id"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user_team(db: AsyncSession,user_id: int,team_id: Optional[int]) -> Optional[User]:
        """привязка пользователя к команде"""
        user = await UserRepository.get_user_by_id(db, user_id)
        if user:
            user.member_of_team = team_id
            await db.commit()
            await db.refresh(user)

        return user


class TeamRepository:
    """Репозиторий для команд"""
    @staticmethod
    async def get_teams(db: AsyncSession,skip: int = 0,limit: int = 100) -> List[Team]:
        """получение информации о команде"""
        result = await db.execute(select(Team).offset(skip).limit(limit))
        return result.scalars().all()


    @staticmethod
    async def get_team_by_id(db: AsyncSession,team_id: int) -> Optional[Team]:
        """получение информации о команде по ее id"""
        result = await db.execute(select(Team).where(Team.team_id == team_id))
        return result.scalar_one_or_none()


    @staticmethod
    async def get_team_by_invite_code(db: AsyncSession,invite_code: str) -> Optional[Team]:
        """получение информации о команде по пригласительному коду"""
        result = await db.execute(select(Team).where(Team.invite_code == invite_code))
        return result.scalar_one_or_none()


    @staticmethod
    async def create_team(db: AsyncSession,team_data: dict) -> Team:
        """создание новой команды"""
        return await db_error_handler.create_operation(db, Team, team_data)


    @staticmethod
    async def update_team(db: AsyncSession,team_id: int,team_data: dict) -> Optional[Team]:
        """обновление данных о команде"""
        return await db_error_handler.update_operation(db,TeamRepository.get_team_by_id,team_id,team_data)


    @staticmethod
    async def delete_team(db: AsyncSession,team_id: int) -> bool:
        """удаление команды"""
        return await db_error_handler.delete_operation(db,TeamRepository.get_team_by_id,team_id)
       
        
class MeetingRepository:
    """Репозиторий для встреч"""
    @staticmethod
    async def get_meetings_by_filters(db: AsyncSession,skip: int = 0,limit: int = 100,start_date: Optional[datetime] = None,end_date: Optional[datetime] = None,user_id: Optional[int] = None) -> List[Meeting]:
        """ получение данных о встрече по фильтрам"""
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
        """получение данных о встрече по ее id"""
        result = await db.execute(select(Meeting).where(Meeting.meeting_id == meeting_id))
        return result.scalar_one_or_none()


    @staticmethod
    async def get_user_meetings(db: AsyncSession,user_id: int) -> List[Meeting]:
        """получение назначенных встреч для пользователя"""
        result = await db.execute(select(Meeting).
                                  where(Meeting.participants.any(id=user_id)).
                                  order_by(Meeting.meeting_date))
        return result.scalars().all()


    @staticmethod
    async def create_meeting(db: AsyncSession,meeting_data: dict) -> Optional[Meeting]:
        """создание новой встречи"""
        return await db_error_handler.create_operation(db, Meeting, meeting_data)


    @staticmethod
    async def update_meeting(db: AsyncSession,meeting_id: int,meeting_data: dict) -> Optional[Meeting]:
        """обновление данных встречи"""
        return await db_error_handler.update_operation(db,MeetingRepository.get_meeting_by_id,meeting_id,meeting_data)


    @staticmethod
    async def delete_meeting(db: AsyncSession,meeting_id: int) -> bool:
        """удаление встречи"""
        return await db_error_handler.delete_operation(db,MeetingRepository.get_meeting_by_id,meeting_id)
    
    
    @staticmethod
    async def check_meeting_conflicts(db: AsyncSession,user_ids: List[int],meeting_date: datetime,duration_minutes: int,exclude_meeting_id: Optional[int] = None) -> List[Meeting]:
        """проверка пересечения встреч"""
        meeting_end = meeting_date + timedelta(minutes=duration_minutes)
        query = (select(Meeting).join(Meeting.participants).where(User.id.in_(user_ids)))

        if exclude_meeting_id:
            query = query.where(Meeting.meeting_id != exclude_meeting_id)
            
        result = await db.execute(query)
        
        all_meetings = result.scalars().all()

        conflict_meetings = []
        
        for meeting in all_meetings:
            existing_end = meeting.meeting_date + timedelta(minutes=meeting.duration_minutes)
            if meeting_date < existing_end and meeting_end > meeting.meeting_date:
                conflict_meetings.append(meeting)

        return conflict_meetings
            

class CommentRepository:
    """Репозиторий для комментариев"""
    @staticmethod
    async def create_comment(db: AsyncSession,comment_data: dict) -> Comment:
        """создать комментарий"""
        return await db_error_handler.create_operation(db, Comment, comment_data)

    @staticmethod
    async def get_comments_by_task_id(db: AsyncSession, task_id: int) -> List[Comment]:
        """получение комментариев по id задачи"""
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