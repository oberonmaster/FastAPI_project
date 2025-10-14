from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from typing import List, Optional
from datetime import datetime, timedelta
from app.database.database import async_session_maker
from app.database.models import Evaluation, Task, User, RoleEnum
from app.users import current_active_user
from app.schemas import EvaluationCreate, EvaluationRead


router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/", response_model=EvaluationRead)
async def create_evaluation(
        evaluation: EvaluationCreate,
        current_user: User = Depends(current_active_user)
):
    if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    async with async_session_maker() as session:
        task = await session.get(Task, evaluation.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status != "completed":
            raise HTTPException(
                status_code=400,
                detail="Can only evaluate completed tasks"
            )

        if task.task_checker != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not task checker"
            )

        existing_eval = await session.execute(
            select(Evaluation).where(
                Evaluation.task_id == evaluation.task_id,
                Evaluation.evaluator_id == current_user.id
            )
        )
        if existing_eval.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Task already evaluated by this user"
            )

        db_evaluation = Evaluation(
            evaluation_value=evaluation.evaluation_value,
            evaluation_name=evaluation.evaluation_name,
            evaluation_comment=evaluation.evaluation_comment,
            task_id=evaluation.task_id,
            evaluator_id=current_user.id
        )
        session.add(db_evaluation)
        await session.commit()
        await session.refresh(db_evaluation)
        return db_evaluation


@router.get("/", response_model=List[EvaluationRead])
async def get_evaluations(
        skip: int = 0,
        limit: int = 100,
        task_id: Optional[int] = None,
        user_id: Optional[int] = None,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        query = select(Evaluation)

        if task_id:
            query = query.where(Evaluation.task_id == task_id)
        if user_id:
            query = query.where(Evaluation.evaluator_id == user_id)

        if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]:
            query = query.join(Evaluation.task).where(
                (Task.task_executor == current_user.id) |
                (Task.task_checker == current_user.id)
            )

        result = await session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()


@router.get("/my-evaluations", response_model=List[EvaluationRead])
async def get_my_evaluations(
        current_user: User = Depends(current_active_user)
):
    """Получить оценки текущего пользователя"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Evaluation).join(Evaluation.task).where(
                Task.task_executor == current_user.id
            ).order_by(Evaluation.created_at.desc())
        )
        return result.scalars().all()


@router.get("/user/{user_id}/average")
async def get_user_average_rating(
        user_id: int,
        period_days: Optional[int] = 30,
        current_user: User = Depends(current_active_user)
):

    """Получить средний рейтинг пользователя за период"""
    if current_user.id != user_id and current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    async with async_session_maker() as session:
        start_date = datetime.utcnow() - timedelta(days=period_days)

        result = await session.execute(
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


@router.get("/{evaluation_id}", response_model=EvaluationRead)
async def get_evaluation(
        evaluation_id: int,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        evaluation = await session.get(Evaluation, evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        task = evaluation.task
        if (current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager] and
                task.task_executor != current_user.id and task.task_checker != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        return evaluation


@router.put("/{evaluation_id}", response_model=EvaluationRead)
async def update_evaluation(
        evaluation_id: int,
        evaluation_update: EvaluationCreate,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        evaluation = await session.get(Evaluation, evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        if evaluation.evaluator_id != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not evaluation author"
            )

        evaluation.evaluation_value = evaluation_update.evaluation_value
        evaluation.evaluation_name = evaluation_update.evaluation_name
        evaluation.evaluation_comment = evaluation_update.evaluation_comment

        await session.commit()
        await session.refresh(evaluation)
        return evaluation


@router.delete("/{evaluation_id}")
async def delete_evaluation(
        evaluation_id: int,
        current_user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        evaluation = await session.get(Evaluation, evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        if evaluation.evaluator_id != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not evaluation author"
            )

        await session.delete(evaluation)
        await session.commit()
        return {"message": "Evaluation deleted successfully"}