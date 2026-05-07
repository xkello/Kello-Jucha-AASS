from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import absences, audit, auth, manager, teams, timesheets, users
from app.core.database import get_db

app = FastAPI(
    title="Timesheet & Absence Portal API",
    version="1.0.0",
    description="Production-like MVP backend for timesheets, absences, approvals, teams, and audit logging.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(timesheets.router)
app.include_router(absences.router)
app.include_router(audit.router)
app.include_router(manager.router)


@app.get("/")
def root():
    return {"message": "Timesheet & Absence Portal API", "docs": "/docs"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
