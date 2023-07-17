from .chats import ChatService
from .locations import LocationService
from .offers import OfferService
from .reviews import ReviewService
from .users import RelationService, UserService

user_service = UserService()
relation_service = RelationService()
location_service = LocationService()
review_service = ReviewService()
offer_service = OfferService()
chat_service = ChatService()
