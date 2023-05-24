from fastapi import APIRouter, Query

from ..util.types import LongitudeCoordinate, LatitudeCoordinate


router = APIRouter(
    prefix = "/offers",
    tags = ["offers"]
)

@router.get("/around")
def get_offers_in_area(
        long: LongitudeCoordinate,
        lat: LatitudeCoordinate,
        radius: float,
        activities: list[str] = Query(None)):
    pass

@router.post("/")
def create_offer():
    pass

@router.put("/{offer_id}")
def contact_offerer(offer_id: int):
    pass


