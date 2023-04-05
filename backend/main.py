from fastapi import FastAPI, Query

from .routers import users, offers, locations, events

app = FastAPI()

app.include_router(locations.router)
app.include_router(users.router)
app.include_router(offers.router)
# app.include_router(events.router)


#### Offers and events



