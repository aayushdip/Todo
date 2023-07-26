from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import engine
import app.models as models
from app.hashing_password import hash_password
from app.models.user import User
from app.models.todo import Todo
from app.schemas.user_schema import UserCreate, UserRead
from app.schemas.todo_schema import TodoCreate, TodoUpdate, TodoRead
from app.schemas.token_schema import Token
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from app.dependencies import (
    get_db,
    create_access_token,
    authenticate_user,
    has_access,
)
from datetime import timedelta
from app.settings import setting_object


models.user.Base.metadata.create_all(bind=engine)
models.todo.Base.metadata.create_all(bind=engine)

app = FastAPI()
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException


@app.post("/users", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    already_existing_user = db.query(User).filter(User.email == user.email).first()
    if already_existing_user:
        raise HTTPException(
            status_code=400, detail="User already exist in tha database"
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


@app.get("/users/me", response_model=UserRead)
def read_user(user: User = Depends(has_access), db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).get(user.id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except SQLAlchemyError as e:
        print("Error caught:", e)
        raise HTTPException(status_code=500, detail="Database error")


@app.post("/todos", response_model=TodoRead)
def create_todo(
    todo: TodoCreate,
    user: User = Depends(has_access),
    db: Session = Depends(get_db),
):
    try:
        db_todo = Todo(title=todo.title, description=todo.description, owner_id=user.id)

        db.add(db_todo)
        db.commit()
        db.refresh(db_todo)
        return db_todo
    except SQLAlchemyError as e:
        print("Error caught:", e)
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/todos/{todo_id}", response_model=TodoRead)
def read_todo(
    todo_id: int, user: User = Depends(has_access), db: Session = Depends(get_db)
):
    try:
        db_todo = db.query(Todo).get(todo_id)
        if db_todo is None:
            raise HTTPException(status_code=404, detail="Todo not found")
        if db_todo.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this todo",
            )

        return db_todo
    except SQLAlchemyError as e:
        print("Error caught:", e)
        raise HTTPException(status_code=500, detail="Database error")


@app.put("/todos/{todo_id}", response_model=TodoRead)
def update_todo(
    todo_id: int,
    todo: TodoUpdate,
    user: User = Depends(has_access),
    db: Session = Depends(get_db),
):
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


@app.delete("/todos/{todo_id}")
def delete_todo(
    todo_id: int, user: User = Depends(has_access), db: Session = Depends(get_db)
):
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


@app.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
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
