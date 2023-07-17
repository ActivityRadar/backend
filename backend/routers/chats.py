from datetime import datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException

from backend.database.models.users import Message
from backend.database.service import chat_service, relation_service
from backend.routers.users import ApiUser

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/")
async def start_chat(user: ApiUser, partner_id: PydanticObjectId) -> PydanticObjectId:
    ids = [user.id, partner_id]
    relation = await relation_service.has_relation_to(*ids)
    if not relation:
        raise HTTPException(401, "Users dont have relation yet!")

    chat = await chat_service.get_or_create(relation)

    return chat.id


@router.get("/")
async def poll_users_chats(user: ApiUser, last_poll_time: datetime):
    messages, poll_time = await chat_service.get_new_messages(user, last_poll_time)

    return {"messages": messages, "poll_time": poll_time}


@router.post("/message")
async def send_message(user: ApiUser, chat_id: PydanticObjectId, message: Message):
    message.sender = user.id
    message.time = datetime.utcnow()

    if len(message.text) > 1000:
        raise HTTPException(401, "Text too long!")

    await chat_service.send_message(user, chat_id, message)
