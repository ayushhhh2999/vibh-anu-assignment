from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth import router as auth_router
from app.db import Base, engine
from app import models

from fastapi import Depends
from app.leads import router as leads_router
from app.models import User
from app.permissions import require_roles


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Vibh-Anu Lead Management API",
    lifespan=lifespan,
)
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "VIBANU_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(leads_router)

@app.get("/")
def home():
    return {"message": "Welcome to Vibhanu Assignment FastAPI application!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/marketing/check", tags=["Authorization"])
def marketing_check(
    current_user: User = Depends(require_roles("marketing")),
):
    return {
        "message": "Marketing access granted",
        "user": current_user.full_name,
        "role": current_user.role,
    }