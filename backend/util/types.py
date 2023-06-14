from datetime import datetime, time
from typing import Annotated

from fastapi import Query

### Geospatial types
LongitudeCoordinate = Annotated[float, Query(ge=-180.0, le=180.0)]
LatitudeCoordinate = Annotated[float, Query(ge=-90.0, le=90.0)]

LongLat = tuple[LongitudeCoordinate, LatitudeCoordinate]
BoundingBox = tuple[LongLat, LongLat]
Polygon = list[LongLat]


def to_4_corners(b: BoundingBox) -> list[list[float]]:
    lleft, lright, uleft, uright = [b[0], [b[0][1], b[1][0]], [b[1][0], b[0][1]], b[1]]
    return [lleft, lright, uleft, uright]


### Time types
Time = time
Datetime = datetime

# A type for time pairs like 17:00 - 19:30
TimeSlotFlexible = tuple[Time, Time]

# A type for time pairs like 2023-03-31T12:30:00 - 2023-03-31T14:30:00
TimeSlotFixed = tuple[Datetime, Datetime]


### Trust scores
TrustScore = int
UserTrustScore = TrustScore
LocationTrustScore = TrustScore
