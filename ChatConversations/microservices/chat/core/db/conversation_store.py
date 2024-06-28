# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import time
from logging.config import dictConfig

import bson.errors as BsonError
from bson.objectid import ObjectId
from conf.config import Settings
from core.common.constant import Literals, Message
from core.common.logger import Logger
from core.db.mongo_conn import MongoClient
from core.util.exception import ConversationApiError, ConversationManagerError, ValidationError
from schema.message import MessageModel
from schema.payload import ConversationModel
from schema.type import MongoObjectId

settings = Settings()
dictConfig(Logger().model_dump())
logger = logging.getLogger(settings.APP_NAME)


class ConversationStore:
    def __init__(
        self,
        user: str,
        conversation_id: str = None,
        message_id: str = None,
    ):
        self.user = user
        self.conversation_id = conversation_id
        self.message_id = message_id

    def initialize_storage(self) -> None:
        self.db_client = MongoClient.get_db_client()
        collection_name = MongoClient.get_collection_name(Literals.conversations)

        self.collection = self.db_client[collection_name]

    async def save_conversation(self, conversation: ConversationModel) -> MongoObjectId:
        """Stores a new conversation into the storage."""

        try:
            logger.info(conversation.messages)
            inserted_conv = await self.collection.insert_one(
                conversation.model_dump(by_alias=True, mode="json", exclude={"conversation_id"})
            )
            self.conversation_id = str(inserted_conv.inserted_id)
            return self.conversation_id

        except Exception as e:
            logger.error(e)
            raise ConversationManagerError()

    async def update_conversation(self, message: MessageModel, update_time: int) -> bool:
        """Add a new message/chat to an existing conversation and updates its metadata."""

        try:
            _id = ObjectId(self.conversation_id)
            update_result = await self.collection.update_one(
                {"_id": _id},
                {
                    "$push": {"messages": message.model_dump(by_alias=True, mode="json")},
                    "$inc": {"message_count": 1},
                    "$set": {"updated_at": update_time},
                },
            )

            if update_result.matched_count != 1:
                return False

            return True

        except BsonError.InvalidId as e:
            logger.error(e)
            raise ValidationError(Message.Error.INVALID_CONVERSATION_ID)

        except Exception as e:
            logger.error(e)
            raise ConversationManagerError()

    async def get_all_conversations_by_user(self) -> list[dict]:
        conversation_list: list = []
        try:
            cursor = self.collection.find({"user_id": self.user}, {"messages": 0})
            async for document in cursor:
                conversation_list.append(document)

            return conversation_list

        except Exception as e:
            logger.error(e)
            raise ConversationApiError()

    async def get_conversation_by_id(self) -> dict | None:
        if not self.conversation_id:
            logger.error(Message.Conversation.CONVERSATION_ID_NOT_SET)
            raise ConversationApiError(Message.Conversation.CONVERSATION_ID_NOT_SET)

        try:
            _id = ObjectId(self.conversation_id)
            response: dict | None = await self.collection.find_one({"_id": _id, "user_id": self.user})

            return response

        except BsonError.InvalidId as e:
            logger.error(e)
            raise ConversationApiError(Message.Error.INVALID_CONVERSATION_ID)

        except Exception as e:
            logger.error(e)
            raise ConversationManagerError()

    async def delete_conversation(self) -> bool:
        if self.conversation_id is None:
            logger.error(Message.Conversation.CONVERSATION_ID_NOT_SET)
            raise ConversationManagerError()

        try:
            _id = ObjectId(self.conversation_id)
            delete_result = await self.collection.delete_one({"_id": _id, "user_id": self.user})

            delete_count = delete_result.deleted_count
            logger.info(f"Deleted {delete_count} documents!")

            return True if delete_count == 1 else False

        except BsonError.InvalidId as e:
            logger.error(e)
            raise ConversationApiError(Message.Error.INVALID_CONVERSATION_ID)

        except Exception as e:
            logger.error(e)
            raise ConversationManagerError()
