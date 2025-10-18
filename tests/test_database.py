import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text, select
from contextlib import asynccontextmanager

from app.database.database import (
    engine,
    async_session_maker,
    Base
)
from app.database.models import User, Task, Team, Evaluation, Comment


class TestDatabaseConfiguration:
    """Тесты конфигурации базы данных"""

    def test_engine_creation(self):
        """Тест создания engine"""
        assert engine is not None
        assert str(engine.url).startswith('postgresql+asyncpg://')

    def test_async_session_maker_creation(self):
        """Тест создания async_session_maker"""
        assert async_session_maker is not None

        from sqlalchemy.orm import sessionmaker
        assert isinstance(async_session_maker, sessionmaker)

        assert async_session_maker.kw.get('expire_on_commit') == False

        test_engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

        session = TestSession()
        assert isinstance(session, AsyncSession)
        assert session.is_active

    def test_base_metadata(self):
        """Тест что Base metadata содержит все таблицы"""
        expected_tables = {
            'users', 'tasks', 'teams', 'meetings',
            'evaluations', 'comments', 'meeting_participants'
        }
        actual_tables = set(Base.metadata.tables.keys())

        for table in expected_tables:
            assert table in actual_tables, f"Table {table} not found in metadata"

class TestDatabaseSession:
    """Тесты работы с сессиями"""

    @pytest.mark.asyncio
    async def test_get_async_session(self):
        """Тест получения асинхронной сессии"""
        test_engine = create_async_engine(
            "sqlite+aiosqlite:///./test_session.db",
            connect_args={"check_same_thread": False},
        )

        TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

        @asynccontextmanager
        async def test_get_async_session():
            async with TestSessionLocal() as session:
                yield session

        async with test_get_async_session() as session:
            assert isinstance(session, AsyncSession)
            assert session.is_active

    @pytest.mark.asyncio
    async def test_session_commit_rollback(self, test_session):
        """Тест commit и rollback операций"""
        user = User(
            email="test@session.com",
            hashed_password="hashed_password",
            username="testsessionuser"
        )
        test_session.add(user)
        await test_session.commit()

        result = await test_session.execute(select(User).where(User.email == "test@session.com"))
        saved_user = result.scalar_one_or_none()
        assert saved_user is not None
        assert saved_user.email == "test@session.com"

        new_user = User(
            email="rollback@test.com",
            hashed_password="pwd",
            username="rollbackuser"
        )
        test_session.add(new_user)
        await test_session.rollback()

        result = await test_session.execute(select(User).where(User.email == "rollback@test.com"))
        rolled_back_user = result.scalar_one_or_none()
        assert rolled_back_user is None

    @pytest.mark.asyncio
    async def test_session_query_operations(self, test_session):
        """Тест операций запросов"""
        user1 = User(
            email="query1@test.com",
            hashed_password="pwd1",
            username="queryuser1"
        )
        user2 = User(
            email="query2@test.com",
            hashed_password="pwd2",
            username="queryuser2"
        )
        test_session.add_all([user1, user2])
        await test_session.commit()

        result = await test_session.execute(select(User))
        users = result.scalars().all()
        assert len(users) >= 2

        result = await test_session.execute(
            select(User).where(User.email == "query1@test.com")
        )
        user = result.scalar_one()
        assert user.email == "query1@test.com"

    @pytest.mark.asyncio
    async def test_session_delete_operations(self, test_session):
        """Тест операций удаления"""
        user = User(
            email="delete@test.com",
            hashed_password="pwd",
            username="deleteuser"
        )
        test_session.add(user)
        await test_session.commit()

        await test_session.delete(user)
        await test_session.commit()

        result = await test_session.execute(select(User).where(User.email == "delete@test.com"))
        deleted_user = result.scalar_one_or_none()
        assert deleted_user is None


class TestDatabaseTables:
    """Тесты создания таблиц"""

    @pytest.mark.asyncio
    async def test_create_db_and_tables(self):
        """Тест создания таблиц БД"""
        test_engine = create_async_engine(
            "sqlite+aiosqlite:///./test_create.db",
            connect_args={"check_same_thread": False},
        )

        try:
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with test_engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                )
                users_table = result.fetchone()
                assert users_table is not None

                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
                )
                tasks_table = result.fetchone()
                assert tasks_table is not None

        finally:
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await test_engine.dispose()

    @pytest.mark.asyncio
    async def test_table_relationships(self, test_session):
        """Тест связей между таблицами"""
        team = Team(team_name="Test Team")
        test_session.add(team)
        await test_session.commit()
        await test_session.refresh(team)

        user = User(
            email="relationship@test.com",
            hashed_password="pwd",
            username="relationshipuser",
            member_of_team=team.team_id
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        task = Task(
            task_name="Test Task",
            task_description="Test Description",
            task_executor=user.id,
            team_id=team.team_id
        )
        test_session.add(task)
        await test_session.commit()
        await test_session.refresh(task)

        assert user.member_of_team == team.team_id
        assert task.task_executor == user.id
        assert task.team_id == team.team_id


class TestDatabaseModels:
    """Тесты моделей базы данных"""

    @pytest.mark.asyncio
    async def test_user_model_creation(self, test_session):
        """Тест создания модели User"""
        user = User(
            email="model@test.com",
            hashed_password="hashed_password",
            username="modeluser",
            is_active=True,
            is_verified=False,
            is_superuser=False,
            role="user"
        )

        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        assert user.id is not None
        assert user.email == "model@test.com"
        assert user.username == "modeluser"
        assert user.role == "user"
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_task_model_creation(self, test_session):
        """Тест создания модели Task"""
        user = User(
            email="taskcreator@test.com",
            hashed_password="pwd",
            username="taskcreator"
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        task = Task(
            task_name="Test Task Model",
            task_description="Test task description",
            status="open",
            task_executor=user.id
        )

        test_session.add(task)
        await test_session.commit()
        await test_session.refresh(task)

        assert task.task_id is not None
        assert task.task_name == "Test Task Model"
        assert task.status == "open"
        assert task.task_executor == user.id
        assert task.created_at is not None

    @pytest.mark.asyncio
    async def test_team_model_creation(self, test_session):
        """Тест создания модели Team"""
        team = Team(
            team_name="Test Team Model",
            invite_code="test123"
        )

        test_session.add(team)
        await test_session.commit()
        await test_session.refresh(team)

        assert team.team_id is not None
        assert team.team_name == "Test Team Model"
        assert team.invite_code == "test123"
        assert team.created_at is not None

    @pytest.mark.asyncio
    async def test_evaluation_model_creation(self, test_session):
        """Тест создания модели Evaluation"""
        user = User(
            email="evaluator@test.com",
            hashed_password="pwd",
            username="evaluator"
        )
        task = Task(task_name="Task for Evaluation")

        test_session.add_all([user, task])
        await test_session.commit()
        await test_session.refresh(user)
        await test_session.refresh(task)

        evaluation = Evaluation(
            evaluation_value=5,
            evaluation_name="Excellent work",
            evaluation_comment="Great job!",
            task_id=task.task_id,
            evaluator_id=user.id
        )

        test_session.add(evaluation)
        await test_session.commit()
        await test_session.refresh(evaluation)

        assert evaluation.evaluation_id is not None
        assert evaluation.evaluation_value == 5
        assert evaluation.task_id == task.task_id
        assert evaluation.evaluator_id == user.id

    @pytest.mark.asyncio
    async def test_comment_model_creation(self, test_session):
        """Тест создания модели Comment"""

        user = User(
            email="commenter@test.com",
            hashed_password="pwd",
            username="commenter"
        )
        task = Task(task_name="Task for Comment")

        test_session.add_all([user, task])
        await test_session.commit()
        await test_session.refresh(user)
        await test_session.refresh(task)


        comment = Comment(
            content="This is a test comment",
            task_id=task.task_id,
            author_id=user.id
        )

        test_session.add(comment)
        await test_session.commit()
        await test_session.refresh(comment)

        assert comment.comment_id is not None
        assert comment.content == "This is a test comment"
        assert comment.task_id == task.task_id
        assert comment.author_id == user.id


class TestDatabaseConstraints:
    """Тесты ограничений базы данных"""

    @pytest.mark.asyncio
    async def test_user_email_unique_constraint(self, test_session):
        """Тест уникальности email пользователя"""
        user1 = User(
            email="unique@test.com",
            hashed_password="pwd1",
            username="user1"
        )
        test_session.add(user1)
        await test_session.commit()

        user2 = User(
            email="unique@test.com",
            hashed_password="pwd2",
            username="user2"
        )
        test_session.add(user2)


        with pytest.raises(Exception):
            await test_session.commit()

        await test_session.rollback()

    @pytest.mark.asyncio
    async def test_evaluation_value_constraint(self, test_session):
        """Тест ограничения значения оценки"""
        task = Task(task_name="Constraint Task")
        test_session.add(task)
        await test_session.commit()
        await test_session.refresh(task)


        evaluation = Evaluation(
            evaluation_value=6,
            task_id=task.task_id
        )
        test_session.add(evaluation)

        with pytest.raises(Exception):
            await test_session.commit()

        await test_session.rollback()


class TestDatabaseErrorHandling:
    """Тесты обработки ошибок базы данных"""

    @pytest.mark.asyncio
    async def test_session_error_handling(self, test_session):
        """Тест обработки ошибок сессии"""
        with pytest.raises(Exception):
            await test_session.execute(text("INVALID SQL STATEMENT"))

        assert test_session.is_active

    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Тест обработки ошибок соединения"""
        invalid_engine = create_async_engine(
            "postgresql+asyncpg://invalid:password@invalid_host:5432/invalid_db"
        )

        with pytest.raises(Exception):
            async with invalid_engine.connect():
                pass


class TestDatabasePerformance:
    """Тесты производительности базы данных"""

    @pytest.mark.asyncio
    async def test_bulk_operations(self, test_session):
        """Тест массовых операций"""
        users = [
            User(
                email=f"bulk{i}@test.com",
                hashed_password=f"pwd{i}",
                username=f"bulkuser{i}"
            )
            for i in range(10)
        ]

        test_session.add_all(users)
        await test_session.commit()

        result = await test_session.execute(select(User).where(User.email.like("bulk%@test.com")))
        bulk_users = result.scalars().all()
        assert len(bulk_users) == 10

    @pytest.mark.asyncio
    async def test_query_performance(self, test_session):
        """Тест производительности запросов"""
        import time

        users = [
            User(
                email=f"perf{i}@test.com",
                hashed_password="pwd",
                username=f"perfuser{i}"
            )
            for i in range(50)
        ]
        test_session.add_all(users)
        await test_session.commit()

        start_time = time.time()

        result = await test_session.execute(
            select(User).where(User.email.like("perf%@test.com"))
        )
        users = result.scalars().all()

        end_time = time.time()
        execution_time = end_time - start_time

        assert len(users) == 50
        assert execution_time < 1.0


class TestDatabaseEdgeCases:
    """Тесты edge cases базы данных"""

    @pytest.mark.asyncio
    async def test_null_values_handling(self, test_session):
        """Тест обработки NULL значений"""
        user = User(
            email="nulltest@test.com",
            hashed_password="pwd",
            username=None
        )
        test_session.add(user)
        await test_session.commit()

        result = await test_session.execute(
            select(User).where(User.email == "nulltest@test.com")
        )
        saved_user = result.scalar_one()
        assert saved_user.username is None

    @pytest.mark.asyncio
    async def test_empty_strings_handling(self, test_session):
        """Тест обработки пустых строк"""
        task = Task(
            task_name="Empty Test Task",
            task_description="",  # Пустая строка
            status="open"
        )
        test_session.add(task)
        await test_session.commit()

        result = await test_session.execute(
            select(Task).where(Task.task_name == "Empty Test Task")
        )
        saved_task = result.scalar_one()
        assert saved_task.task_description == ""