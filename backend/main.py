from fastapi import FastAPI, Query

from .database.connection import init as init_db
from .routers import users, offers, locations

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()

    app.include_router(locations.router)
    app.include_router(users.router)
    app.include_router(offers.router)
    # app.include_router(events.router)
