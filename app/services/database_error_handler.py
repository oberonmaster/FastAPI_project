"""try/except обработчик для различных операций"""
from typing import Any, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError


class DatabaseErrorHandler:
    """Обработчик ошибок"""

    # try/except для баз данных
    @staticmethod
    async def execute_with_error_handling(db: AsyncSession,
                                          operation: Callable,
                                          *args,
                                          **kwargs) -> Any:
        """
        передаем базу, тип операции и арги с кваргами
        """
        try:
            result = await operation(*args, **kwargs)
            return result
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Database error in {operation.__name__}: {e}")
            return None
        except Exception as e:
            await db.rollback()
            print(f"Unexpected error in {operation.__name__}: {e}")
            return None


    # crud-операций
    @staticmethod
    async def create_operation(db: AsyncSession,
                               model_class: Any,
                               data: dict) -> Any:
        """
        Операция содзания для передачи в execute_with_error_handling
        """
        async def _create():
            obj = model_class(**data)
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj

        return await DatabaseErrorHandler.execute_with_error_handling(db, _create)

    @staticmethod
    async def update_operation(db: AsyncSession,
                               get_method: Callable,
                               object_id: int,
                               update_data: dict) -> Any:
        """
        Операция обновления для передачи в execute_with_error_handling
        """
        async def _update():
            obj = await get_method(db, object_id)
            if obj:
                for key, value in update_data.items():
                    setattr(obj, key, value)
                await db.commit()
                await db.refresh(obj)
            return obj

        return await DatabaseErrorHandler.execute_with_error_handling(db, _update)

    @staticmethod
    async def delete_operation(db: AsyncSession,
                               get_method: Callable,
                               object_id: int) -> bool:
        """
        Операция удаления для передачи в execute_with_error_handling
        """
        async def _delete():
            obj = await get_method(db, object_id)
            if obj:
                await db.delete(obj)
                await db.commit()
                return True
            return False

        result = await DatabaseErrorHandler.execute_with_error_handling(db, _delete)
        return result if result is not None else False


# Создаем экземпляр для использования
db_error_handler = DatabaseErrorHandler()
