from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.todo_schema import TodoCreate, TodoUpdate, TodoRead
from app.dependencies import (
    get_db,
    has_access,
)
from .crud import (
    todo_create_post,
    todo_read_get,
    todo_update_delete,
    todo_update_put,
)

router = APIRouter()


@router.post("/todos", response_model=TodoRead)
def create_todo(
    todo: TodoCreate,
    user: User = Depends(has_access),
    db: Session = Depends(get_db),
):
    return todo_create_post(todo, user, db)


@router.get("/todos/{todo_id}", response_model=TodoRead)
def read_todo(
    todo_id: int, user: User = Depends(has_access), db: Session = Depends(get_db)
):
    return todo_read_get(todo_id, user, db)


@router.put("/todos/{todo_id}", response_model=TodoRead)
def update_todo(
    todo_id: int,
    todo: TodoUpdate,
    user: User = Depends(has_access),
    db: Session = Depends(get_db),
):
    return todo_update_put(todo_id, todo, user, db)


@router.delete("/todos/{todo_id}")
def delete_todo(
    todo_id: int, user: User = Depends(has_access), db: Session = Depends(get_db)
):
    return todo_update_delete(todo_id, user, db)
