"""

"""
# TODO две строки между классами



from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database.database import get_async_session
from app.database.models import User, RoleEnum, TaskStatusEnum
from app.database.repository import user_repo, task_repo, comment_repo
from app.users import current_active_user
from app.schemas import TaskCreate, TaskRead, CommentCreate, CommentRead


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskRead)
async def create_task(
        task: TaskCreate,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """создание задачи"""
    if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    # проверка исполнителя
    if task.task_executor and task.task_executor > 0:
        executor = await user_repo.get_user_by_id(db, task.task_executor)
        if not executor:
            raise HTTPException(
                status_code=404,
                detail="Executor not found"
            )
        if (current_user.member_of_team and
                executor.member_of_team != current_user.member_of_team and
                current_user.role != RoleEnum.admin):
            raise HTTPException(
                status_code=403,
                detail="Executor is not in your team"
            )
    # создание задачи
    task_data = {
        "task_name": task.task_name,
        "task_description": task.task_description,
        "task_executor": task.task_executor if task.task_executor and task.task_executor > 0 else None,
        "task_checker": current_user.id,
        "team_id": current_user.member_of_team,
        "deadline": task.deadline,
        "status": TaskStatusEnum.open
    }

    db_task = await task_repo.creaate_task(db,task_data)
    return TaskRead.model_validate(db_task)


@router.get("/", response_model=List[TaskRead])
async def get_tasks(
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatusEnum] = None,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """получение списка задач"""
    if current_user.role in [RoleEnum.admin]:
        tasks = await task_repo.get_tasks_by_filters(db,skip,limit,status)
    elif current_user.role in [RoleEnum.team_admin, RoleEnum.manager]:
        tasks = await task_repo.get_tasks_by_filters(db, skip, limit, status, current_user.member_of_team)
    else:
        tasks = await task_repo.get_user_tasks(db, current_user.id)

    return [TaskRead.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
        task_id: int,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """получение задачи по id"""
    task = await task_repo.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    if (current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager] and
            task.task_executor != current_user.id and task.task_checker != current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    return TaskRead.model_validate(task)


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
        task_id: int,
        task_update: TaskCreate,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """обновление задачи"""
    task = await task_repo.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    if (current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager] and
            task.task_checker != current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return TaskRead.model_validate(task)


@router.patch("/{task_id}/status")
async def update_task_status(
        task_id: int,
        status: TaskStatusEnum,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """обновление статуса задачи"""
    task = await task_repo.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    if task.task_executor != current_user.id and task.task_checker != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    updated_task = await task_repo.update_task_status(db, task_id, status)

    return {"message": f"Task status updated to {status}"}


@router.delete("/{task_id}")
async def delete_task(
        task_id: int,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """отмена задачи"""
    task = await task_repo.get_task_by_id(db, task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    await db.delete(task)
    await db.commit()
    return {"message": "Task deleted successfully"}


@router.post("/{task_id}/comments", response_model=CommentRead)
async def add_comment(
        task_id: int,
        comment: CommentCreate,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """добавление комментариев"""
    task = await task_repo.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    if (task.task_executor != current_user.id and
            task.task_checker != current_user.id and
            current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    comment_data = {
        "content": comment.content,
        "task_id": task_id,
        "author_id": current_user.id
    }

    db_comment = await comment_repo.create_comment(db, comment_data)
    return CommentRead.model_validate(db_comment)


@router.get("/{task_id}/comments", response_model=List[CommentRead])
async def get_task_comments(
        task_id: int,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """получение комментария к задаче"""
    task = await task_repo.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    if (task.task_executor != current_user.id and
            task.task_checker != current_user.id and
            current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    comments = await comment_repo.get_comments_by_task_id(db, task_id)
    return [CommentRead.model_validate(comment) for comment in comments]
