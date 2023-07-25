import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from .database.connection import init as init_db
from .routers import admin, auth, chats, locations, offers, users

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

    with open("openapi.json", "w") as f:
        json.dump(
            get_openapi(
                title=app.title,
                version=app.version,
                openapi_version=app.openapi_version,
                description=app.description,
                routes=app.routes,
                # openapi_prefix=app.openapi_prefix,
            ),
            f,
        )
