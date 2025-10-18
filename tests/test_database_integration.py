import pytest
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import create_async_engine
from app.database.database import Base
from app.database.models import User, Task, Team


class TestDatabaseIntegration:
    """Интеграционные тесты базы данных"""

    @pytest.mark.asyncio
    async def test_all_tables_have_columns(self):
        """Тест что все таблицы имеют колонки"""
        test_engine = create_async_engine(
            "sqlite+aiosqlite:///./test_integration.db",
            connect_args={"check_same_thread": False},
        )

        try:
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with test_engine.connect() as conn:
                inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))

                tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())
                expected_tables = ['users', 'tasks', 'teams', 'meetings', 'evaluations', 'comments']

                for table in expected_tables:
                    assert table in tables, f"Table {table} not created"


                    columns = await conn.run_sync(
                        lambda sync_conn: inspector.get_columns(table)
                    )
                    assert len(columns) > 0, f"Table {table} has no columns"

        finally:
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await test_engine.dispose()

    @pytest.mark.asyncio
    async def test_foreign_key_relationships(self, test_session):
        """Тест связей по внешним ключам"""
        team = Team(team_name="FK Test Team")
        test_session.add(team)
        await test_session.commit()
        await test_session.refresh(team)

        user = User(
            email="fk@test.com",
            hashed_password="pwd",
            username="fkuser",
            member_of_team=team.team_id
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        task = Task(
            task_name="FK Test Task",
            task_executor=user.id,
            team_id=team.team_id
        )
        test_session.add(task)
        await test_session.commit()
        await test_session.refresh(task)

        assert user.member_of_team == team.team_id
        assert task.task_executor == user.id
        assert task.team_id == team.team_id


        result = await test_session.execute(
            select(User).where(User.id == user.id)
        )
        loaded_user = result.scalar_one()

        result = await test_session.execute(
            select(Task).where(Task.task_id == task.task_id)
        )
        loaded_task = result.scalar_one()


        assert loaded_user.member_of_team == team.team_id
        assert loaded_task.task_executor == user.id
        assert loaded_task.team_id == team.team_id