from typing import Annotated

from fastapi import Query

LongitudeCoordinate = Annotated[float, Query(ge=-180.0, le=180.0)]
LatitudeCoordinate = Annotated[float, Query(ge=-90.0, le=90.0)]

