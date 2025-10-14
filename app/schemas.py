from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
from fastapi_users import schemas

class UserRead(schemas.BaseUser[int]):
    username: Optional[str] = None
    role: Optional[str] = None
    member_of_team: Optional[int] = None

class UserCreate(schemas.BaseUserCreate):
    username: Optional[str] = None

class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str] = None


class TeamBase(BaseModel):
    team_name: str

class TeamCreate(TeamBase):
    pass

class TeamRead(TeamBase):
    team_id: int
    team_admin: Optional[int] = None
    invite_code: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    task_name: str
    task_description: Optional[str] = None
    deadline: Optional[datetime] = None

class TaskCreate(TaskBase):
    task_executor: Optional[int] = None

class TaskRead(TaskBase):
    task_id: int
    status: str
    task_executor: Optional[int] = None
    task_checker: Optional[int] = None
    team_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class MeetingBase(BaseModel):
    meeting_name: str
    meeting_description: Optional[str] = None
    meeting_date: datetime
    duration_minutes: Optional[int] = 60

class MeetingCreate(MeetingBase):
    participant_ids: list[int] = []

class MeetingRead(MeetingBase):
    meeting_id: int
    meeting_admin: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class EvaluationBase(BaseModel):
    evaluation_value: int
    evaluation_name: Optional[str] = None
    evaluation_comment: Optional[str] = None

class EvaluationCreate(EvaluationBase):
    task_id: int

class EvaluationRead(EvaluationBase):
    evaluation_id: int
    task_id: int
    evaluator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    task_id: int

class CommentRead(CommentBase):
    comment_id: int
    task_id: int
    author_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str