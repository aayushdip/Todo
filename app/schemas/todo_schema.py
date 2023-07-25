from pydantic import BaseModel

from app.schemas.user_schema import UserRead


# Pydantic model for creating a new todo
class TodoCreate(BaseModel):
    title: str
    description: str
    owner_id: int


# Pydantic model for updating an existing todo
class TodoUpdate(BaseModel):
    title: str
    description: str


# Pydantic model for reading a todo
class TodoRead(BaseModel):
    id: int
    title: str
    description: str
    owner: UserRead

    class Config:
        orm_mode = True
