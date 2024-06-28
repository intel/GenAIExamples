# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
from logging.config import dictConfig
from typing import Any

import motor.motor_asyncio as motor
from conf.config import Settings
from core.common.constant import Literals, Message
from core.common.logger import Logger
from core.util.exception import ConversationManagerError

settings = Settings()
dictConfig(Logger().model_dump())
logger = logging.getLogger(settings.APP_NAME)


class MongoClient:
    mongo_host = settings.MONGO_HOST
    mongo_port = settings.MONGO_PORT
    conn_url = f"mongodb://{mongo_host}:{mongo_port}/"
    db_name = settings.MONGODB_DB_NAME

    collections = {
        Literals.conversations: settings.CONVERSATION_TABLE,
    }

    @staticmethod
    def get_collection_name(collection_type: str) -> str:
        collection_name: str = MongoClient.collections.get(collection_type)

        if not collection_name:
            logger.error(Message.DB.COLLECTION_NAME_ERROR)
            raise ConversationManagerError()

        return collection_name

    @staticmethod
    def get_db_client() -> Any:
        try:
            client = motor.AsyncIOMotorClient(MongoClient.conn_url)
            db = client[settings.MONGODB_DB_NAME]
            return db

        except Exception as e:
            logger.error(e)
            raise ConversationManagerError()
