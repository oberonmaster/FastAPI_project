"""
Основной скрипт создания и запуска приложения + админ
"""
import os
import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin
from app.database.database import engine, Base


from app.admin import (SimpleAuth,
                       UserAdmin,
                       TeamAdmin,
                       TaskAdmin,
                       MeetingAdmin)

app = FastAPI(title="My FastAPI App")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-secret"))

Base.metadata.create_all(bind=engine)


#Admin panel
SECRET_KEY = os.getenv("SECRET_KEY")
admin = Admin(app=app,
              engine=engine,
              authentication_backend=SimpleAuth(SECRET_KEY),
              base_url="/admin")
admin.add_view(UserAdmin)
admin.add_view(TeamAdmin)
admin.add_view(TaskAdmin)
admin.add_view(MeetingAdmin)

def main():
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=8000,
                reload=True)


if __name__ == "__main__":
    main()
