"""users manipulation"""
import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import Depends, Request
from fastapi_users import (BaseUserManager,
                           FastAPIUsers,
                           IntegerIDMixin)
from fastapi_users.authentication import (AuthenticationBackend,
                                          BearerTransport,
                                          JWTStrategy)
from fastapi_users.db import SQLAlchemyUserDatabase
from app.database.database import get_async_session
from app.database.models import User

load_dotenv()
SECRET = os.getenv("SECRET_KEY")


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """class user manager"""
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self,
                                user: User,
                                request: Optional[Request] = None):
        print(f"User {user.id} has registered.")


async def get_user_db():
    """getting user from db"""
    async with get_async_session() as session:
        yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """getting user manager"""
    yield UserManager(user_db)

# JWT backend
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    """getting jwt"""
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
