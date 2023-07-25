from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.models.user import User
from typing import Annotated
from app.database import SessionLocal
from fastapi.security import (
    HTTPAuthorizationCredentials,
)
from jose.exceptions import JOSEError
from app.hashing_password import verify_password
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.schemas.token_schema import TokenData
from app import settings
from app.settings import setting_object


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user(db: Session, username: str):
    user_info = db.query(User).filter(User.username == username).first()

    if user_info:
        return user_info


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, setting_object.SECRET_KEY, algorithm=setting_object.ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(settings.oauth2_scheme)],
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, setting_object.SECRET_KEY, algorithms=[setting_object.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def has_access(
    credentials: HTTPAuthorizationCredentials = Depends(settings.security),
    db=Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            key="secret",
            options={
                "verify_signature": False,
                "verify_aud": False,
                "verify_iss": False,
            },
        )
        username: str = payload.get("sub")
        if username is None:
            raise setting_object.credentials_exception
        token_data = TokenData(username=username)
    except JOSEError as e:  # catches any exception
        raise HTTPException(status_code=401, detail=str(e))
    user = get_user(db, username=token_data.username)
    if user is None:
        raise setting_object.credentials_exception
    return user
