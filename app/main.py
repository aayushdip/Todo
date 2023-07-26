from fastapi import FastAPI
import uvicorn
from app.database import engine
import app.models as models
from .routers import todo, user, login

models.user.Base.metadata.create_all(bind=engine)
models.todo.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(todo.router, prefix="/todos", tags=["Todos"])
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(login.router, prefix="/login", tags=["Login"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
