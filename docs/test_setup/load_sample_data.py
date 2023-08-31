import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Any, Coroutine

import munch
import numpy as np
import overpass
from beanie import init_beanie
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.append("../../")

from backend.database.connection import client
from backend.database.models.locations import (
    LocationDetailedDb,
    LocationShortDb,
    ReviewsSummary,
)
from backend.database.models.shared import LocationCreators
from backend.database.service import location_service
from backend.util import constants

client = AsyncIOMotorClient(constants.MONGODB_CONNECTION_STRING)


async def init_db():
    await init_beanie(
        database=client[constants.DATABASE_NAME], document_models=[LocationDetailedDb]
    )
    await init_beanie(
        database=client[constants.DATABASE_NAME], document_models=[LocationShortDb]
    )


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


def load_data_from_overpass(tile: list[float]):
    api = overpass.API(timeout=1000)

    south, west, north, east = tile
    query = f"""
        [out:json][bbox:{south},{west},{north},{east}];
        nwr[sport];
        convert item ::id=id(),::=::,::geom=geom(),_osm_type=type();
        out geom;
    """
    geometries: dict[str, Any] = api.get(query, build=False)

    query = f"""
        [out:json][bbox:{south},{west},{north},{east}];
        nwr[sport];
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
        "activity_types": loc.tags.sport.split(";"),
        "location": dict(loc.center),
        "creation": {
            "created_by": LocationCreators.OSM,
            "date": datetime.strptime(loc.timestamp, constants.DATE_FMT),
        },
        "osm_id": loc.id,
        "tags": {k: v for k, v in loc.tags.items() if k != "sport"},
        "trust_score": 1000,
        "reviews": ReviewsSummary(average_rating=0, count=0, recent=[]),
        "last_modified": datetime.strptime(loc.timestamp, constants.DATE_FMT),
        "photos": [],
    }
    if loc.tags.name is not None:
        d |= {"name": loc.tags.name}
    if loc.geometry is not None:
        d |= {"geometry": dict(loc.geometry)}
    else:
        d |= {"geometry": None}
    return d


async def insert_all_service(elements):
    for e in elements:
        await location_service._insert(LocationDetailedDb(**osm_to_mongo(e)))


async def reset_collections():
    await LocationShortDb.find({}).delete()
    await LocationDetailedDb.find({}).delete()


async def work_tile(tile: list[float]):
    south, west, north, east = tile
    print(f"Loading data for tile: {south},{west},{north},{east}...")
    data = load_data_from_overpass(tile)
    print(f"Data loaded for tile: {south},{west},{north},{east}")

    elements = data["elements"]
    await insert_all_service(elements)


def split_tiles(south: float, west: float, north: float, east: float):
    vertical = np.linspace(south, north, num=10)
    horizontal = np.linspace(west, east, num=10)

    tiles = []
    for i in range(len(vertical) - 1):
        for j in range(len(horizontal) - 1):
            tiles.append(
                (vertical[i], horizontal[j], vertical[i + 1], horizontal[j + 1])
            )

    return tiles


def parse_args():
    parser = argparse.ArgumentParser(
        prog="OSM Sports Data Fetcher",
        description="Fetches data via the Overpass API and inserts it into the mongo DB",
    )

    parser.add_argument("--reset", type=bool, default=False)
    parser.add_argument("--bbox", nargs=4, type=float, default=[47, 5.8, 55, 15])

    return parser.parse_args()


async def main():
    await init_db()

    args = parse_args()

    if args.reset:
        await reset_collections()

    tiles = split_tiles(*args.bbox)

    funs: list[Coroutine] = []
    for tile in tiles:
        funs.append(work_tile(tile))

    await asyncio.gather(*funs)


if __name__ == "__main__":
    asyncio.run(main())
