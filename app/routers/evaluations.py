"""маршруты для оценок"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database.database import get_async_session
from app.database.models import Evaluation, User, RoleEnum
from app.database.repository import evaluation_repo, task_repo
from app.dependencies import get_evaluation_access_user
from app.fastapi_users import current_active_user
from app.schemas import EvaluationCreate, EvaluationRead


router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/", response_model=EvaluationRead)
async def create_evaluation(
        evaluation: EvaluationCreate,
        current_user: User = Depends(get_evaluation_access_user),
        db: AsyncSession = Depends(get_async_session)
):
    """создание оценки"""
    # получение задачи через репозиторий
    task = await task_repo.get_task_by_id(db, evaluation.task_id)
    # TODO вынести в отдельный handler
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # бизнес-логика
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Can only evaluate completed tasks")

    if task.task_checker != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not task checker")

    # проверка дублей через репозиторий
    if await evaluation_repo.check_duplicate_evaluations(db, evaluation.task_id, current_user.id):
        raise HTTPException(status_code=400, detail="Task already evaluated by this user")

    # создание оценки через репозиторий
    evaluation_data = {
        "evaluation_value": evaluation.evaluation_value,
        "evaluation_name": evaluation.evaluation_name,
        "evaluation_comment": evaluation.evaluation_comment,
        "task_id": evaluation.task_id,
        "evaluator_id": current_user.id
    }

    db_evaluation = await evaluation_repo.create_evaluation(db, evaluation_data)
    if not db_evaluation:
        raise HTTPException(status_code=500, detail="Failed to create evaluation")

    return EvaluationRead.model_validate(db_evaluation)


@router.get("/", response_model=List[EvaluationRead])
async def get_evaluations(
        skip: int = 0,
        limit: int = 100,
        task_id: Optional[int] = None,
        user_id: Optional[int] = None,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    # получение оценки через репозиторий
    evaluations = await evaluation_repo.get_evaluations_by_filters(db, skip, limit, task_id, user_id)

    # проверка прав доступа
    if current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]:
        evaluations = [evaluation for evaluation in evaluations if
                       evaluation.task.task_executor == current_user.id or
                       evaluation.task.task_checker == current_user.id]
        return [EvaluationRead.model_validate(ev) for ev in evaluations]
    return None


@router.get("/my-evaluations", response_model=List[EvaluationRead])
async def get_my_evaluations(
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)
):
    """Получить оценки текущего пользователя"""
    evaluations = await evaluation_repo.get_user_evaluations(db, current_user.id)
    return [EvaluationRead.model_validate(ev) for ev in evaluations]


@router.get("/user/{user_id}/average")
async def get_user_average_rating(
    user_id: int,
    period_days: Optional[int] = 30,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получить средний рейтинг пользователя за период"""
    if current_user.id != user_id and current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    result = await evaluation_repo.get_user_average_rating(db, user_id, period_days)
    return result


@router.get("/{evaluation_id}", response_model=EvaluationRead)
async def get_evaluation(
        evaluation_id: int,
        current_user: User = Depends(current_active_user),
):
    """получение оценки"""
    evaluation = await evaluation_repo.get_evaluation_by_id(Evaluation, evaluation_id)

    # TODO вынести в отдельный handler
    if not evaluation:
        raise HTTPException(
            status_code=404,
            detail="Evaluation not found"
        )

    task = evaluation.task
    if (current_user.role not in [RoleEnum.admin, RoleEnum.team_admin, RoleEnum.manager] and
            task.task_executor != current_user.id and task.task_checker != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return EvaluationRead.model_validate(evaluation)

@router.put("/{evaluation_id}", response_model=EvaluationRead)
async def update_evaluation(
    evaluation_id: int,
    evaluation_update: EvaluationCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """обновление оценки"""
    evaluation_data = {
        "evaluation_value": evaluation_update.evaluation_value,
        "evaluation_name": evaluation_update.evaluation_name,
        "evaluation_comment": evaluation_update.evaluation_comment
    }

    updated_evaluation = await evaluation_repo.update_evaluation(db, evaluation_id, evaluation_data)
    if not updated_evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found or update failed")

    return EvaluationRead.model_validate(updated_evaluation)


@router.delete("/{evaluation_id}")
async def delete_evaluation(
    evaluation_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """удаление оценки"""
    success = await evaluation_repo.delete_evaluation(db, evaluation_id)
    # TODO вынести в отдельный handler
    if not success:
        raise HTTPException(status_code=404, detail="Evaluation not found or delete failed")

    return {"message": "Evaluation deleted successfully"}
