from datetime import datetime, time
from typing import Annotated

from fastapi import Query

LongitudeCoordinate = Annotated[float, Query(ge=-180.0, le=180.0)]
LatitudeCoordinate = Annotated[float, Query(ge=-90.0, le=90.0)]

LongLat = tuple[LongitudeCoordinate, LatitudeCoordinate]

Time = time
Datetime = datetime

# A type for time pairs like 17:00 - 19:30
TimeSlotFlexible = tuple[Time, Time]

# A type for time pairs like 2023-03-31T12:30:00 - 2023-03-31T14:30:00
TimeSlotFixed = tuple[Datetime, Datetime]

