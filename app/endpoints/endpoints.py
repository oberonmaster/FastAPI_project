# """ ендпоинты сервиса """
# from fastapi import Depends, HTTPException
# from sqlalchemy.orm import Session
#
# from app.database import schemas
# from app.endpoints import crud
# from main import fastapi_app
#
#
# # TODO users
# # registration:
# # - login
# # - password
# #
# # login/logout
# #
# # roles:
# # - ordinary
# # - manager
# # - admin
# #
# # update profile
# #
# # permanent delete profile
#
#
# @fastapi_app.post("/users/", response_model=schemas.User)
# def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     return crud.create_user(db=db, user=user)
#
# @fastapi_app.get("/users/", response_model=list[schemas.User])
# def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = crud.get_users(db, skip=skip, limit=limit)
#     return users
#
# @fastapi_app.get("/users/{user_id}", response_model=schemas.User)
# def read_user(user_id: int, db: Session = Depends(get_db)):
#     db_user = crud.get_user(db, user_id=user_id)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user
#
# # TODO teams
# # create team(only admin)
# #
# # add/remove users from team
# #
# # get_team_list
# #
# # set_team_roles (ordinary, manager)
#
# # TODO tasks
# # greate_task (only admin)
# #
# # set_worker
# #
# # description(status, end_time)
# #
# # update/remove
# #
# # comments
# #
# # status:
# # - start
# # - in_process
# # - finished
#
#
# # TODO task_rating
#
# # TODO meetings
#
# # TODO calendar
#
# # TODO admin
