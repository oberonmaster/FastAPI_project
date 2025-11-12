""" Модели данных для заполнения базы """
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import (Table,
                        Column,
                        Integer,
                        String,
                        ForeignKey,
                        Boolean,
                        TIMESTAMP,
                        func,
                        CheckConstraint,
                        Enum,
                        UniqueConstraint,
                        Text)
from app.database.database import Base
from sqlalchemy.orm import relationship, synonym
from fastapi_users.password import PasswordHelper
import enum


meeting_participants = Table(
    "meeting_participants",
    Base.metadata,
    Column("meeting_id", Integer, ForeignKey("meetings.meeting_id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)

_password_helper = PasswordHelper()


class RoleEnum(str, enum.Enum):
    user = "user"
    manager = "manager"
    team_admin = "team_admin"
    admin = "admin"


class TaskStatusEnum(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"


class User(SQLAlchemyBaseUserTable[int], Base):
    """main info"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, unique=True)

    # Fields
    # Поля
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.user, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    # Связи
    member_of_team = Column(Integer, ForeignKey("teams.team_id"), nullable=True)
    team = relationship("Team", back_populates="members", foreign_keys=[member_of_team], lazy="joined")
    admin_of = relationship("Team", back_populates="admin", uselist=False, foreign_keys="Team.team_admin", lazy="selectin")
    tasks_assigned = relationship("Task", back_populates="executor", foreign_keys="Task.task_executor", lazy="selectin")
    tasks_checked = relationship("Task", back_populates="checker", foreign_keys="Task.task_checker", lazy="selectin")
    evaluations_given = relationship("Evaluation", back_populates="evaluator", foreign_keys="Evaluation.evaluator_id", lazy="selectin")
    meetings = relationship("Meeting", secondary=meeting_participants, back_populates="participants", lazy="selectin")
    comments_written = relationship("Comment", back_populates="author", lazy="selectin")

    def __str__(self):
        return self.username

    def _get_password(self) -> str:
        return self.hashed_password

    def _set_password(self, raw_password: str) -> None:
        if raw_password:
            self.hashed_password = _password_helper.hash(raw_password)

    password = synonym("hashed_password", descriptor=property(_get_password, _set_password))


class Task(Base):
    __tablename__ = "tasks"
    task_id = Column(Integer, primary_key=True, index=True, unique=True)

    # Fields
    # Поля
    task_name = Column(String, nullable=False)
    task_description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.open, nullable=False)
    deadline = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    # Связи
    task_executor = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    task_checker = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=True)
    executor = relationship("User", back_populates="tasks_assigned", foreign_keys=[task_executor], lazy="joined")
    checker = relationship("User", back_populates="tasks_checked", foreign_keys=[task_checker], lazy="joined")
    team = relationship("Team", back_populates="tasks", lazy="joined")
    evaluations = relationship("Evaluation", back_populates="task", cascade="all, delete-orphan", lazy="selectin")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan", lazy="selectin")

    def average_rating(self):
        """Вычисляем среднюю оценку (None если оценок нет)."""
        if not self.evaluations:
            return None
        vals = [e.evaluation_value for e in self.evaluations if e.evaluation_value is not None]
        return sum(vals) / len(vals) if vals else None


class Team(Base):
    __tablename__ = "teams"
    team_id = Column(Integer, primary_key=True, index=True, unique=True)

    # Fields
    # Поля
    team_name = Column(String, unique=True, index=True)
    invite_code = Column(String, unique=True, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    # Связи
    team_admin = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin = relationship("User", back_populates="admin_of", foreign_keys=[team_admin], uselist=False, lazy="joined")
    members = relationship("User", back_populates="team", foreign_keys="User.member_of_team", lazy="selectin", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="team", lazy="selectin")


class Meeting(Base):
    __tablename__ = "meetings"
    meeting_id = Column(Integer, primary_key=True, index=True, unique=True)

    # Fields
    # Поля
    meeting_name = Column(String, nullable=False)
    meeting_description = Column(Text, nullable=True)
    meeting_date = Column(TIMESTAMP(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=60)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    # Связи
    meeting_admin = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    admin = relationship("User", foreign_keys=[meeting_admin], lazy="joined")
    participants = relationship("User", secondary=meeting_participants, back_populates="meetings", lazy="selectin")


class Evaluation(Base):
    __tablename__ = "evaluations"
    evaluation_id = Column(Integer, primary_key=True, index=True, unique=True)

    # Fields
    # Поля
    evaluation_name = Column(String, nullable=True)
    evaluation_value = Column(Integer, nullable=False)
    evaluation_comment = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("evaluation_value >= 1 AND evaluation_value <= 5", name="ck_evaluation_value_range"),
        UniqueConstraint("task_id", "evaluator_id", name="uq_task_evaluator"),
    )

    # Relations
    # Связи
    task_id = Column(Integer, ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    evaluator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    task = relationship("Task", back_populates="evaluations", foreign_keys=[task_id], lazy="joined")
    evaluator = relationship("User", back_populates="evaluations_given", foreign_keys=[evaluator_id], lazy="joined")


class Comment(Base):
    __tablename__ = "comments"
    comment_id = Column(Integer, primary_key=True, index=True, unique=True)

    # Fields
    # Поля
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    # Связи
    task_id = Column(Integer, ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    task = relationship("Task", back_populates="comments", foreign_keys=[task_id], lazy="joined")
    author = relationship("User", back_populates="comments_written", foreign_keys=[author_id], lazy="joined")