from fastapi import FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from app.hashing_password import hash_password
from app.models.user import User
from app.models.todo import Todo
from app.schemas.user_schema import UserCreate
from app.schemas.todo_schema import TodoCreate, TodoUpdate
from fastapi.security import OAuth2PasswordRequestForm
from app.dependencies import (
    create_access_token,
    authenticate_user,
)
from datetime import timedelta
from app.settings import setting_object
from sqlalchemy.exc import SQLAlchemyError


def user_create_post(user: UserCreate, db: Session):
    already_existing_user = db.query(User).filter(User.email == user.email).first()
    if already_existing_user:
        raise HTTPException(
            status_code=400, detail="User already exists in the database"
        )
    try:
        db_user = User(
            username=user.username,
            fullname=user.fullname,
            email=user.email,
            hashed_password=hash_password(user.password),
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        print("Error caught:", e)
        raise HTTPException(status_code=500, detail="Database error")


def user_read_get(user: User, db: Session):
    try:
        db_user = db.query(User).get(user.id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except SQLAlchemyError as e:
        print("Error caught:", e)
        raise HTTPException(status_code=500, detail="Database error")


def todo_create_post(todo: TodoCreate, user: User, db: Session):
    try:
        db_todo = Todo(title=todo.title, description=todo.description, owner_id=user.id)
        db.add(db_todo)
        db.commit()
        db.refresh(db_todo)
        return db_todo
    except SQLAlchemyError as e:
        print("Error caught:", e)
        raise HTTPException(status_code=500, detail="Database error")


def todo_read_get(todo_id: int, user: User, db: Session):
    try:
        db_todo = db.query(Todo).get(todo_id)
        if db_todo is None:
            raise HTTPException(status_code=404, detail="Post not found")
        if db_todo.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to read this post",
            )
        return db_todo
    except SQLAlchemyError as e:
        print("Error caught:", e)
        raise HTTPException(status_code=500, detail="Database error")


def todo_update_put(todo_id: int, todo: TodoUpdate, user: User, db: Session):
    try:
        db_todo = db.query(Todo).get(todo_id)
        if db_todo is None:
            raise HTTPException(status_code=404, detail="Todo not found")
        if db_todo.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this todo",
            )
        db_todo.title = todo.title
        db_todo.description = todo.description
        db.commit()
        db.refresh(db_todo)
        return db_todo
    except SQLAlchemyError as e:
        print("Error caught:", e)
        raise HTTPException(status_code=500, detail="Database error")


def todo_update_delete(todo_id: int, user: User, db: Session):
    try:
        db_todo = db.query(Todo).get(todo_id)
        if db_todo is None:
            raise HTTPException(status_code=404, detail="Todo not found")

        if db_todo.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this todo",
            )

        db.delete(db_todo)
        db.commit()
        return {"message": "Todo deleted"}

    except SQLAlchemyError as e:
        print("Error caught:", e)
        raise HTTPException(status_code=500, detail="Database error")


def login(form_data: OAuth2PasswordRequestForm, db: Session):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=setting_object.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
