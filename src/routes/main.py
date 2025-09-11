from fastapi import FastAPI
from src.routes import users

app = FastAPI(title="User & Auth Service")

# Register routes
app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/")
def root():
    return {"message": "User & Authentication Service is running"}
