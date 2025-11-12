import asyncio
import pytest
from typing import AsyncGenerator, Generator

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.database.database import Base, get_async_session
from app.database.models import User
from app.fastapi_users import get_user_db
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.password import PasswordHelper

# Тестовая база данных SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestAsyncSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

password_helper = PasswordHelper()


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def override_get_user_db():
    async with TestAsyncSessionLocal() as session:
        yield SQLAlchemyUserDatabase(session, User)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """Setup and teardown database for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture(scope="function")
def test_client() -> TestClient:
    """Create a test client with overridden dependencies."""
    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[get_user_db] = override_get_user_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_admin_user(test_session: AsyncSession):
    """Создает тестового админа"""
    user = User(
        email="admin@test.com",
        hashed_password=password_helper.hash("admin123"),
        username="testadmin",
        is_active=True,
        is_verified=True,
        is_superuser=True,
        role="admin"
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_regular_user(test_session: AsyncSession):
    """Создает тестового обычного пользователя"""
    user = User(
        email="user@test.com",
        hashed_password=password_helper.hash("user123"),
        username="testuser",
        is_active=True,
        is_verified=True,
        is_superuser=False,
        role="user"
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user