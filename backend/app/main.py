from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    clients,
    accounts,
    positions,
    dashboard,
    banks,
    advisors
)


app = FastAPI(
    title="Wealth MVP"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    clients.router
)

app.include_router(
    accounts.router
)

app.include_router(
    positions.router
)

app.include_router(
    dashboard.router
)

app.include_router(
    banks.router
)

app.include_router(
    advisors.router
)


@app.get("/")
def root():
    return {
        "status": "running"
    }