from fastapi import FastAPI

from app.api import (
    clients,
    accounts,
    positions,
    dashboard
)


app = FastAPI(
    title="Wealth MVP"
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



@app.get("/")
def root():
    return {
        "status": "running"
    }