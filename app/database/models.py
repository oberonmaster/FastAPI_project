""" Модели данных для заполнения базы """

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, TIMESTAMP, func
from app.database.database import Base
from datetime import datetime, timezone


class User(Base):
    """main info"""
    __tablename__ = "users"
    id = Column(Integer,
                     primary_key=True,
                     index=True,
                     unique=True)

    # Fields
    username = Column(String,
                      unique=True,
                      index=True)
    email = Column(String,
                   unique=True,
                   index=True)
    hashed_password = Column(String,
                             nullable=False)
    is_active = Column(Boolean,
                       default=True)
    is_superuser = Column(Boolean,
                          default=False)
    is_verified = Column(Boolean,
                         default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    member_of_team = Column(Integer,
                            ForeignKey("teams.team_id"),
                            nullable=True)


class Task(Base):
    """main info"""
    __tablename__ = "tasks"
    task_id = Column(Integer,
                     primary_key=True,
                     index=True,
                     unique=True)

    # Fields
    task_name = Column(String)

    # Relations
    task_executor = Column(Integer,
                           ForeignKey("users.id"))


class Team(Base):
    """main info"""
    __tablename__ = "teams"
    team_id = Column(Integer,
                     primary_key=True,
                     index=True,
                     unique=True)

    # Fields
    team_name = Column(String,
                       unique=True,
                       index=True)

    # Relations
    team_admin = Column(Integer,
                        ForeignKey("users.id"))


class Meeting(Base):
    """main info"""
    __tablename__ = "meetings"
    meeting_id = Column(Integer,
                        primary_key=True,
                        index=True,
                        unique=True)

    # Fields
    meeting_name = Column(String)


class Evaluation(Base):
    """main info"""
    __tablename__ = "evaluations"
    evaluation_id = Column(Integer,
                           primary_key=True,
                           index=True,
                           unique=True)
    name = Column(String)

    # Fields
    evaluation_value = Column(Integer)

    # Relations
    task_rating = Column(Integer,
                         ForeignKey("tasks.task_id"))
