# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
from logging.config import dictConfig

from conf.config import Settings
from core.chat_model.llm_interface import LlmInterface
from core.common.constant import Message
from core.common.logger import Logger
from core.util.exception import ConversationManagerError

settings = Settings()
dictConfig(Logger().model_dump())
logger = logging.getLogger(settings.APP_NAME)


class LlmFactory:
    # Store all llm classes mapped with a string identifier
    llm_objects: dict[str, LlmInterface] = {}

    def register(self, model_type: str, llm_object: LlmInterface) -> None:
        """Store the model name and its corresponding object for the llm."""

        # Check whether the model_type is already registered.
        if LlmFactory.llm_objects.get(model_type):
            return

        LlmFactory.llm_objects[model_type] = llm_object
        logger.info(f"Loaded and registered : {model_type}")

    @staticmethod
    def create(model_type: str) -> LlmInterface:
        """Fetch and return the llm class for the given model_type."""

        try:
            if not model_type:
                logger.error(Message.Plugin.Llm.MODEL_NOT_PROVIDED)
                raise ConversationManagerError()

            # Get the llm object from llm_objects dict store
            return LlmFactory.llm_objects[model_type]

        except KeyError:
            logger.error(Message.Plugin.Llm.UNREGISTERED_LLM)
            raise ConversationManagerError()
