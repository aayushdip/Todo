from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserRead
from app.dependencies import (
    get_db,
    has_access,
)
from .crud import (
    user_create_post,
    user_read_get,
)


router = APIRouter()


@router.post("/users", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return user_create_post(user, db)


@router.get("/users/me", response_model=UserRead)
def read_user(user: User = Depends(has_access), db: Session = Depends(get_db)):
    return user_read_get(user, db)
