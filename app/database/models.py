""" Модели данных для заполнения базы """

from sqlalchemy import Column, Integer, String
from app.database.database import Base


class User(Base):
    """main info"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)

    # Fields
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

class Team(Base):
    """main info"""
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)

    # Fields
    team_name = Column(String, unique=True, index=True)

    # Relations
    """one to one """

    """one to many"""
    # team_admin =
    # team_member =

    """many to many"""

class Task(Base):
    """main info"""
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)

    # Fields
    task_name = Column(String)

    # Relations
    """one to one """
    # task_executor

    """one to many"""

    """many to many"""

class Meeting(Base):
    """main info"""
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    # Fields
    meeting_name = Column(String)
    # Relations
    """one to one """

    """one to many"""

    """many to many"""

class Evaluation(Base):
    """main info"""
    __tablename__ = "evalutions"
    id = Column(Integer, primary_key=True, index=True)
    # Fields
    evaluation_name = Column(String)
    # Relations
    """one to one """

    """one to many"""

    """many to many"""







