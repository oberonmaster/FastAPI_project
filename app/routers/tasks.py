from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from typing import List, Optional
from app.database.database import async_session_maker
from app.database.models import Task, User, RoleEnum, TaskStatusEnum, Comment
from app.users import current_active_user
from app.schemas import TaskCreate, TaskRead, CommentCreate, CommentRead

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskRead)
async def create_task(
        task: TaskCreate,
        current_user: User = Depends(current_active_user)
):
    if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    async with async_session_maker() as session:
        if task.task_executor and task.task_executor > 0:
            executor = await session.get(User, task.task_executor)
            if not executor:
                raise HTTPException(status_code=404, detail="Executor not found")

            if (current_user.member_of_team and
                    executor.member_of_team != current_user.member_of_team and
                    current_user.role != RoleEnum.admin):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Executor is not in your team"
                )

        db_task = Task(
            task_name=task.task_name,
            task_description=task.task_description,
            task_executor=task.task_executor if task.task_executor and task.task_executor > 0 else None,
            task_checker=current_user.id,
            team_id=current_user.member_of_team,
            deadline=task.deadline,
            status=TaskStatusEnum.open
        )

        session.add(db_task)
        await session.commit()
        await session.refresh(db_task)
        return db_task


@router.get("/", response_model=List[TaskRead])
async def get_tasks(
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatusEnum] = None,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        query = select(Task)

        if status:
            query = query.where(Task.status == status)

        if current_user.role in [RoleEnum.admin]:
            pass
        elif current_user.role in [RoleEnum.team_admin, RoleEnum.manager]:
            if current_user.member_of_team:
                query = query.where(Task.team_id == current_user.member_of_team)
        else:
            query = query.where(
                (Task.task_executor == current_user.id) |
                (Task.task_checker == current_user.id)
            )

        result = await session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
        task_id: int,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        task = await session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if (current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager] and
                task.task_executor != current_user.id and task.task_checker != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        return task


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
        task_id: int,
        task_update: TaskCreate,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        task = await session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if (current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager] and
                task.task_checker != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        for field, value in task_update.dict(exclude_unset=True).items():
            setattr(task, field, value)

        await session.commit()
        await session.refresh(task)
        return task


@router.patch("/{task_id}/status")
async def update_task_status(
        task_id: int,
        status: TaskStatusEnum,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        task = await session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.task_executor != current_user.id and task.task_checker != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        task.status = status
        await session.commit()

        return {"message": f"Task status updated to {status}"}


@router.delete("/{task_id}")
async def delete_task(
        task_id: int,
        current_user: User = Depends(current_active_user)
):
    if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    async with async_session_maker() as session:
        task = await session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        await session.delete(task)
        await session.commit()
        return {"message": "Task deleted successfully"}


@router.post("/{task_id}/comments", response_model=CommentRead)
async def add_comment(
        task_id: int,
        comment: CommentCreate,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        task = await session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if (task.task_executor != current_user.id and
                task.task_checker != current_user.id and
                current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        db_comment = Comment(
            content=comment.content,
            task_id=task_id,
            author_id=current_user.id
        )
        session.add(db_comment)
        await session.commit()
        await session.refresh(db_comment)
        return db_comment


@router.get("/{task_id}/comments", response_model=List[CommentRead])
async def get_task_comments(
        task_id: int,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        task = await session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if (task.task_executor != current_user.id and
                task.task_checker != current_user.id and
                current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        result = await session.execute(select(Comment).where(Comment.task_id == task_id))
        return result.scalars().all()