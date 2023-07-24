import asyncio
import json
import sys
from datetime import datetime
from typing import Any

import munch
import overpass
from beanie import init_beanie
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.append("../../")

from backend.database.connection import client
from backend.database.models.locations import (
    LocationDetailed,
    LocationDetailedDB,
    LocationShortDB,
)
from backend.database.models.shared import LocationCreators
from backend.database.service import location_service
from backend.util import constants

load_dotenv()
client = AsyncIOMotorClient(constants.MONGODB_CONNECTION_STRING)


async def init_db():
    await init_beanie(database=client.AR, document_models=[LocationDetailedDB])
    await init_beanie(database=client.AR, document_models=[LocationShortDB])


def merge(geometries, centers):
    """Merge center GeoJSON data into geometries as "center" key

    Works inplace on the given geometries dict.
    """

    if centers["osm3s"] != geometries["osm3s"]:
        print("Different timestamps! Data might not match!")
        return
    gs = geometries["elements"]
    cs = centers["elements"]
    for i, c in enumerate(cs):
        if gs[i]["id"] != c["id"]:
            print(f'IDs at {i=} dont match up! {gs[i]["id"]} != {c["id"]}')
            return
        gs[i]["center"] = c["geometry"]


def set_type(response):
    for el in response["elements"]:
        if "_osm_type" not in el["tags"].keys():
            print("_osm_type Value missing!")
            return
        el["type"] = el["tags"]["_osm_type"]
        del el["tags"]["_osm_type"]


def load_data_from_overpass():
    api = overpass.API(timeout=100)

    query = """
        [out:json][timeout:100];
        area[name=Berlin]->.searchHere;
        nwr[sport](area.searchHere);
        convert item ::id=id(),::=::,::geom=geom(),_osm_type=type();
        out geom;
    """
    geometries: dict[str, Any] = api.get(query, build=False)

    query = """
        [out:json][timeout:100];
        area[name=Berlin]->.searchHere;
        nwr[sport](area.searchHere);
        convert item ::id=id(),::geom=geom();
        out center;
    """
    centers = api.get(query, build=False)

    now_str = datetime.now().strftime(constants.DATE_FMT)

    merge(geometries, centers)
    set_type(geometries)

    for loc in geometries["elements"]:
        loc["timestamp"] = now_str

    return geometries


def osm_to_mongo(loc):
    loc = munch.DefaultMunch.fromDict(loc)  # easier access in nested dicts
    d = {
        "_schemaVersion": 1,
        "activity_type": loc.tags.sport,
        "location": dict(loc.center),
        "creation": {
            "created_by": LocationCreators.OSM,
            "date": datetime.strptime(loc.timestamp, constants.DATE_FMT),
        },
        "osm_id": loc.id,
        "tags": {k: v for k, v in loc.tags.items() if k != "sport"},
        "trust_score": 1000,
        "recent_reviews": [],
        "last_modified": datetime.strptime(loc.timestamp, constants.DATE_FMT),
    }
    if loc.tags.name is not None:
        d |= {"name": loc.tags.name}
    if loc.geometry is not None:
        d |= {"geometry": dict(loc.geometry)}
    else:
        d |= {"geometry": None}
    return d


async def insert_all(elements):
    es = [osm_to_mongo(e) for e in elements]
    detailed = [LocationDetailedDB(**e) for e in es]
    ds = await LocationDetailedDB.insert_many(detailed)

    short = [LocationShortDB(**e, id=d) for (e, d) in zip(es, ds.inserted_ids)]
    await LocationShortDB.insert_many(short)


async def insert_all_service(elements):
    for e in elements:
        await location_service._insert(LocationDetailedDB(**osm_to_mongo(e)))


async def reset_collections():
    await LocationShortDB.find({}).delete()
    await LocationDetailedDB.find({}).delete()


async def main():
    await init_db()

    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        await reset_collections()

    try:
        data = load_data_from_overpass()
    except:
        try:
            data = json.load(open("../../sports.json", "r"))
        except:
            print(
                "Can neither access overpass nor find the sports.json file in project."
            )
            sys.exit(1)

    elements = data["elements"]
    await insert_all_service(elements)


if __name__ == "__main__":
    asyncio.run(main())
