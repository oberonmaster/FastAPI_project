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
from fastapi_users.exceptions import UserAlreadyExists
from app.database.models import RoleEnum
from app.schemas import UserCreate



load_dotenv()
SECRET = os.getenv("SECRET_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """class user manager"""
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self,
                                user: User,
                                request: Optional[Request] = None):
        print(f"User {user.id} has registered.")


async def create_admin_user():
    """Создание администратора через UserManager"""
    if not all([ADMIN_EMAIL, ADMIN_PASSWORD]):
        print("Admin credentials not provided in .env")
        return
    try:
        async for user_db in get_user_db():
            async for user_manager in get_user_manager(user_db):
                try:
                    existing_user = await user_manager.get_by_email(ADMIN_EMAIL)
                    if existing_user:
                        print(f"Admin user {ADMIN_EMAIL} already exists")
                        if not existing_user.is_superuser or existing_user.role != RoleEnum.admin:
                            update_dict = {
                                "is_superuser": True,
                                "role": RoleEnum.admin,
                                "is_verified": True
                            }
                            await user_manager.user_db.update(existing_user, update_dict)
                            print(f"Updated existing user {ADMIN_EMAIL} to admin")
                        return

                except Exception:
                    pass

                try:
                    user_create = UserCreate(email=ADMIN_EMAIL,password=ADMIN_PASSWORD,username=ADMIN_USERNAME or ADMIN_EMAIL.split('@')[0])

                    admin_user = await user_manager.create(user_create,safe=False)

                    update_dict = {
                        "is_superuser": True,
                        "role": RoleEnum.admin,
                        "is_verified": True
                    }
                    await user_manager.user_db.update(admin_user, update_dict)

                    print(f"Admin user {ADMIN_EMAIL} created successfully")
                    return

                except UserAlreadyExists:
                    print(f"Admin user {ADMIN_EMAIL} already exists")
                    return

    except Exception as e:
        print(f"Error creating admin user: {e}")


async def get_user_db():
    """getting user from db"""
    async for session in get_async_session():
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
