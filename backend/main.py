import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

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

    for route in app.routes:
        if isinstance(route, APIRoute):
            route: APIRoute = route
            route.operation_id = route.name

    with open("openapi.yaml", "w") as f:
        yaml.dump(
            get_openapi(
                title=app.title,
                version=app.version,
                openapi_version=app.openapi_version,
                description=app.description,
                routes=app.routes,
            ),
            f,
            sort_keys=False,
        )
