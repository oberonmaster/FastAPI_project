"""pydantic schemas"""
from typing import Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, EmailStr
from fastapi_users import schemas

class UserRead(schemas.BaseUser[int]):
    """Verification user"""
    username: Optional[str] = None
    role: Optional[str] = None
    member_of_team: Optional[int] = None

class UserCreate(schemas.BaseUserCreate):
    """Verification user create"""
    username: Optional[str] = None

class UserUpdate(schemas.BaseUserUpdate):
    """Verification user update"""
    username: Optional[str] = None

class TeamBase(BaseModel):
    """Verification team base model"""
    team_name: str

class TeamCreate(TeamBase):
    """Verification team"""
    pass

class TeamRead(TeamBase):
    """Verification team"""
    team_id: int
    team_admin: Optional[int] = None
    invite_code: Optional[str] = None
    created_at: datetime

    class Config:
        """class configuration"""
        from_attributes = True

class TaskBase(BaseModel):
    """Verification task base model"""
    task_name: str
    task_description: Optional[str] = None
    deadline: Optional[datetime] = None

class TaskCreate(TaskBase):
    """Verification task create"""
    task_executor: Optional[int] = None

class TaskRead(TaskBase):
    """Verification task"""
    task_id: int
    status: str
    task_executor: Optional[int] = None
    task_checker: Optional[int] = None
    team_id: Optional[int] = None
    created_at: datetime

    class Config:
        """class configuration"""
        from_attributes = True

class MeetingBase(BaseModel):
    """Verification meeting base model"""
    meeting_name: str
    meeting_description: Optional[str] = None
    meeting_date: datetime
    duration_minutes: Optional[int] = 60

class MeetingCreate(MeetingBase):
    """Verification meeting create"""
    participant_ids: list[int] = []

class MeetingRead(MeetingBase):
    """Verification meeting"""
    meeting_id: int
    meeting_admin: Optional[int] = None
    created_at: datetime

    class Config:
        """class configuration"""
        from_attributes = True

class EvaluationBase(BaseModel):
    """Verification evaluation base model"""
    evaluation_value: int
    evaluation_name: Optional[str] = None
    evaluation_comment: Optional[str] = None

class EvaluationCreate(EvaluationBase):
    """Verification evaluation create"""
    task_id: int

class EvaluationRead(EvaluationBase):
    """Verification evaluation"""
    evaluation_id: int
    task_id: int
    evaluator_id: Optional[int] = None
    created_at: datetime

    class Config:
        """class configuration"""
        from_attributes = True

class CommentBase(BaseModel):
    """Verification comment base model"""
    content: str

class CommentCreate(CommentBase):
    """Verification of comment create"""
    task_id: int

class CommentRead(CommentBase):
    """Verification of comment"""
    comment_id: int
    task_id: int
    author_id: Optional[int] = None
    created_at: datetime

    class Config:
        """class configuraion"""
        from_attributes = True


class LoginRequest(BaseModel):
    """Verification of login request"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """verification of token response"""
    access_token: str
    token_type: str



class CalendarEventBase(BaseModel):
    """Базовая схема для событий календаря"""
    id: str
    title: str
    start: str
    type: str

class TaskEvent(CalendarEventBase):
    """Схема для задач в календаре"""
    status: str
    description: Optional[str] = None

class MeetingEvent(CalendarEventBase):
    """Схема для встреч в календаре"""
    end: str
    description: Optional[str] = None

class CalendarEventResponse(BaseModel):
    """Общая схема ответа для событий календаря"""
    events: List[Union[TaskEvent, MeetingEvent]]

class DayEventResponse(BaseModel):
    """Схема для событий дня"""
    type: str
    id: int
    title: str
    time: str
    description: Optional[str] = None
    status: Optional[str] = None
    duration: Optional[str] = None

class DayCalendarResponse(BaseModel):
    """Схема ответа для календаря дня"""
    date: str
    events: List[DayEventResponse]
