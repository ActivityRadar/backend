import dotenv
from fastapi import FastAPI

from .database.connection import init as init_db
from .routers import auth, users, offers, locations

dotenv.load_dotenv()

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()

    app.include_router(auth.router)
    app.include_router(locations.router)
    app.include_router(users.router)
    app.include_router(offers.router)
    # app.include_router(events.router)
