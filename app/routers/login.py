from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from app.schemas.token_schema import Token
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from app.dependencies import get_db
from app.routers.crud import login

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    return login(form_data, db)
