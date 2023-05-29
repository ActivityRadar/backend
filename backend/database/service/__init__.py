from .locations import LocationService
from .reviews import ReviewService
from .users import RelationService, UserService

user_service = UserService()
relation_service = RelationService()
location_service = LocationService()
review_service = ReviewService()
