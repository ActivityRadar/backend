import dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database.connection import init as init_db
from .routers import admin, auth, locations, offers, users, chats

dotenv.load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()

    app.include_router(admin.router)
    app.include_router(auth.router)
    app.include_router(locations.router)
    app.include_router(users.router)
    app.include_router(offers.router)
    app.include_router(chats.router)
    # app.include_router(events.router)
