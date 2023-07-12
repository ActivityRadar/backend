from datetime import datetime
from beanie import PydanticObjectId
from beanie.operators import ElemMatch, Push

from backend.database.models.users import (
    Chat,
    Message,
    MessageOut,
    OfferReactionMessage,
    User,
    UserRelation,
)
from backend.util.errors import RelationDoesNotExist


class ChatService:
    async def get(self, id: PydanticObjectId):
        return await Chat.get(id)

    async def create_chat(
        self, relation_id: PydanticObjectId, user_ids: list[PydanticObjectId]
    ) -> Chat:
        chat = await Chat(id=relation_id, users=user_ids, messages=[]).insert()
        return chat

    async def get_or_create(self, relation: UserRelation):
        chat = await self.get(relation.id)  # type: ignore
        if not chat:
            chat = await self.create_chat(relation.id, relation.users)

        return chat

    def get_all_chats(self, user: User):
        return Chat.find(ElemMatch(Chat.users, {"$eq": user.id}))

    async def get_new_messages(
        self, user: User, last_poll: datetime
    ) -> tuple[list[MessageOut], datetime]:
        time_now = datetime.utcnow()

        aggregation_pipeline = [
            # unwind the messages from chats so that every message is one document
            {"$unwind": "$messages"},
            # Only match documents with the timestamp greater than the poll time
            {"$match": {"$expr": {"$gte": [{"$toDate": "$messages.time"}, last_poll]}}},
            # project the needed data for the MessageOut model
            {"$project": {"chat_id": "$_id", "message": "$messages"}},
        ]

        # aggregates messages from the user's chats that are newer than
        # the last poll time
        new_messages = (
            await self.get_all_chats(user)
            .aggregate(
                aggregation_pipeline,
                projection_model=MessageOut,
            )
            .to_list()
        )

        return new_messages, time_now

    async def react_to_offer(
        self, user: User, chat: Chat, offer_id: PydanticObjectId, message: str
    ):
        msg = OfferReactionMessage(
            sender=user.id, time=datetime.utcnow(), text=message, offer_id=offer_id
        )
        await chat.update(Push({Chat.messages: msg}))

    async def send_message(
        self, user: User, chat_id: PydanticObjectId, message: Message
    ):
        chat = await self.get(chat_id)
        if not chat:
            raise ValueError()

        if user.id not in chat.users:
            raise ValueError()

        await chat.update(Push({Chat.messages: message}))
