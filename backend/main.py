import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from .database.connection import init as init_db
from .routers import admin, auth, chats, locations, offers, users
from .util.email import setup_email_server_connection

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

    # init email setup
    setup_email_server_connection()

    # uncomment to generate a schema on startup. Usually only needed once the code is changed.
    # save_schema()


def cleanup_schema(schema):
    # These endpoints receive form bodies which are not described nicely by default.
    # The names look like `Body_unarchive_user_users_reactivate_put`.
    # As each endpoint gets its own schema, even though they are all the same, coming
    # from the OAuth2PasswordRequestForm class, we need to merge them for a nicer schema:
    pw_form_endpoints = [
        ("/auth/token", "post"),
        ("/users/reactivate", "put"),
        ("/users/me/", "delete"),
    ]
    new_schema_name = "LoginBody"
    schema_names = []
    for path, cmd in pw_form_endpoints:
        try:
            d = schema["paths"][path][cmd]["requestBody"]["content"][
                "application/x-www-form-urlencoded"
            ]["schema"]
            r = d["$ref"]
            schema_name = r.split("/")[-1]
            if not schema_name.startswith("Body"):
                continue

            print(schema_name)
            schema_names.append(schema_name)

            d["$ref"] = f"#/components/schemas/{new_schema_name}"
        except:
            print("Maybe some error parsing the schema?")

    if len(schema_names) > 0:
        d = schema["components"]["schemas"]
        d[new_schema_name] = d[schema_names[0]]
        del d[schema_names[0]]

        for name in schema_names[1:]:
            del d[name]

    return schema


def save_schema():
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name

    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    schema = cleanup_schema(schema)

    with open("shared/openapi.yaml", "w") as f:
        yaml.dump(schema, f, sort_keys=False)
