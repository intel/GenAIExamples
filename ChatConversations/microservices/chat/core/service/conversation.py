# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import time
import uuid
from logging.config import dictConfig

import pydantic
from conf.config import Settings
from core.common.constant import Message
from core.common.logger import Logger
from core.db.conversation_store import ConversationStore
from core.service.model_service import SupportedModels
from core.util.chain_utils import AsyncFinalIteratorCallbackHandler, ChainHelper
from core.util.exception import ConversationManagerError, ValidationError
from fastapi import status
from schema.message import InferenceSettings, MessageModel
from schema.payload import (
    ConversationList,
    ConversationModel,
    ConversationModelResponse,
    ConversationRequest,
    UpsertedConversation,
)

settings = Settings()
dictConfig(Logger().model_dump())
logger = logging.getLogger(settings.APP_NAME)


class ConversationBuilder:
    def __init__(
        self,
        user: str,
        conversation_request: ConversationRequest = None,
        conversation_id: str = None,
    ):
        self.user: str = user
        self.user_params: ConversationRequest = conversation_request
        self.conversation_id: str = conversation_id
        self.system_prompt: str = ""
        self.prompt: list[tuple] = []

        if self.user:
            self.initialize_storage()

    def initialize_storage(self):
        try:
            self.conversation_storage = ConversationStore(self.user, conversation_id=self.conversation_id)
            self.conversation_storage.initialize_storage()
        except Exception as e:
            logger.error(e)
            raise e

    def _adapt_messages(self, messages, db_chat_history: list = []) -> str:
        """
        Args:
            messages (str | list):
                Given a messages in ChatML specification, it creates and refines messages
                array to contain list of tuples, each containing either human or ai message.
                If system prompt is present in messages, extracts the system prompts.

            db_chat_history (list):
                If chat history is available from db, it adds the db chat history to the messages
                first.

        Returns :
            The final query from the list of messages.
        """

        query: str = ""
        for message in db_chat_history:
            self.prompt.append(("human", message.human))
            self.prompt.append(("ai", message.assistant))

        if isinstance(messages, str):
            query = messages
            self.prompt.append(("human", messages))
        else:
            for message in messages:
                msg_role = message.get("role")

                if msg_role == "system":
                    self.system_prompt = message["content"]

                elif msg_role == "user":
                    query = message["content"]

                    if type(query) == list:
                        query = ""
                        text_list = [item["text"] for item in message["content"] if item["type"] == "text"]
                        query += "\n".join(text_list)

                    self.prompt.append(("human", query))

                elif msg_role == "assistant":
                    self.prompt.append(("ai", message["content"]))

        logger.debug(self.prompt)

        return query

    def _initialize_conversation_model(self, current_query: str) -> None:
        """Initialize the known values for conversation object
        to be saved in storage.

        This object can contain all messages
        (list of messages).
        """

        self.conversation = ConversationModel(
            user_id=self.user,
            first_query=current_query,
        )

    def _prepare_new_message_model(self, first_query: str, current_query: str, conversation_id: str = None) -> None:
        """Initialize the known values for message object."""

        self.message = MessageModel(message_id=uuid.uuid4().hex, human=current_query)
        """This conversation object contains the message object which will contain
        the new message.

        It represents the created or updated conversation.
        """
        self.upserted_conversation = UpsertedConversation(
            conversation_id=conversation_id,
            user_id=self.user,
            first_query=first_query,
            last_message=self.message,
        )

    async def initialize_new_conversation(self) -> None:
        try:

            query: str = self._adapt_messages(self.user_params.messages)

            self._initialize_conversation_model(query)

            self._prepare_new_message_model(first_query=query, current_query=query)

        except Exception as e:
            logger.error(e)
            raise e

    async def continue_existing_conversation(self) -> None:

        # TODO !!IMPORTANT
        # To remove this redundant call to get existing conversation. Based on UI user flow,
        # user already has fetched conversation by clicking on any item in chat sidebar. This
        # call is right now helping with 2 items - message_history and message_count. Can be cached
        # and this call can be avoided.
        self.conversation: ConversationModel = await self.get_existing_conversation()

        if not self.conversation:
            raise ValidationError(Message.Error.INVALID_CONVERSATION_ID)

        msg_count = self.conversation.message_count
        if msg_count >= settings.MAX_MESSAGE_LENGTH:
            raise ValidationError(
                Message.Error.MAX_MESSAGES_LIMIT_EXCEEDED,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Get previous messages and set message history
        # Retrieve few of the last messages
        messages_history = self.conversation.messages[-settings.MAX_HISTORY_LENGTH :]

        query: str = self._adapt_messages(messages=self.user_params.messages, db_chat_history=messages_history)

        self._prepare_new_message_model(
            first_query=self.conversation.first_query,
            current_query=query,
            conversation_id=self.conversation_id,
        )

    def _build_new_message(self, result: dict, model_display_name: str) -> MessageModel:
        # llm response is in "answer" key for query with context and in "text" key for w/o context.
        answer = result.get("answer")

        # Get the token from result dict()
        input_token = result.get("input_token")
        output_token = result.get("output_token")

        # Create a new message for the conversation, based on query result
        self.message.assistant = answer

        self.message.inference_settings = InferenceSettings(
            model=model_display_name,
            temperature=self.user_params.temperature,
            token_limit=self.user_params.max_tokens,
            input_token=input_token,
            output_token=output_token,
        )

        return self.message

    def _append_new_message(self, message: MessageModel = None, update_time: int = 0) -> ConversationModel:
        """Add a newly created message to current conversation."""

        message: MessageModel = message or self.message

        current_time = update_time or int(time.time())

        # Update conversation object to be saved in storage
        self.conversation.messages.append(message)
        self.conversation.message_count += 1
        self.conversation.updated_at = current_time
        """Update_time implies we are updating an existing conversation.

        If provided, we may not want to set the created_at time for conversation.
        """
        if not update_time:
            self.conversation.created_at = current_time

        return self.conversation

    def _get_upserted_conversation(self, conversation: ConversationModel) -> UpsertedConversation:
        """Get the updated or created conversation with current message.

        Sent as API response.
        """

        # Update the conversation object to be returned as API response
        self.upserted_conversation.conversation_id = conversation.conversation_id
        """use_case is already loaded from request params in case of new conversation.

        However, in case of continuing an existing conversation this might not be present
        in request params. Hence, re-loading it from conversation object.
        """
        self.upserted_conversation.last_message = conversation.messages[-1]
        self.upserted_conversation.message_count = conversation.message_count
        self.upserted_conversation.created_at = conversation.created_at
        self.upserted_conversation.updated_at = conversation.updated_at

        return self.upserted_conversation

    async def _get_query_result(self) -> dict:
        result = await ChainHelper.build_execute_chain(
            self.user,
            self.user_params,
            self.system_prompt,
            self.prompt,
            stream=False,
        )

        return result

    async def stream_and_build_conversation(self):
        callback_handler = AsyncFinalIteratorCallbackHandler()

        task = asyncio.create_task(
            ChainHelper.build_execute_chain(
                self.user,
                self.user_params,
                self.system_prompt,
                self.prompt,
                stream=True,
                callbacks=[callback_handler],
            )
        )

        try:
            async for token in callback_handler.aiter():
                self.message.assistant = token
                self.upserted_conversation.last_message = self.message
                yield self.upserted_conversation.model_dump_json()

        except Exception as e:
            logger.error("Streaming Error: {e}")
            yield f"{Message.Error.STREAMING_ERROR}\n\n"
            raise e

        finally:
            callback_handler.done.set()

        result = await task

        # Once result is available after streaming completes, use it to populate conversation
        # and message object and update the database.
        if self.user:
            _ = await self.build_conversation(result)

        # Return the new message object with required details, to be used by streaming API consumers
        yield self.upserted_conversation.model_dump_json()

    async def build_conversation(self, result: dict = {}) -> UpsertedConversation:
        # Build the appropriate question answering chain and execute it
        query_result = result or await self._get_query_result()

        model_display_name = await SupportedModels.get_model_attribute(
            self.user_params.model, "display_name", self.user
        )
        # Create and set the message based on query result
        message = self._build_new_message(query_result, model_display_name=model_display_name)

        # If conversation_id is present, update existing stored conversation with new message.
        if self.conversation_id:
            is_update_done = True
            time_of_update = int(time.time())
            if self.user:
                is_update_done = await self.conversation_storage.update_conversation(message, time_of_update)

            # If update is successful, then update conversation object with updated data,
            # as update_one method on monogodb does not return the updated document.
            if is_update_done:
                conversation = self._append_new_message(message, time_of_update)
            else:
                raise ConversationManagerError()

        # If conversation_id is not present, a new conversation needs to be created.
        else:
            conversation = self._append_new_message(message)
            if self.user:
                conversation.conversation_id = await self.conversation_storage.save_conversation(conversation)
        return self._get_upserted_conversation(conversation)

    async def get_conversations_for_user(self) -> ConversationList:
        conversations: list[dict] = await self.conversation_storage.get_all_conversations_by_user()
        conversation_list: ConversationList = pydantic.parse_obj_as(ConversationList, conversations)
        return conversation_list

    async def get_existing_conversation(self) -> ConversationModel | None:
        response: dict | None = await self.conversation_storage.get_conversation_by_id()
        self.conversation = pydantic.parse_obj_as(ConversationModel | None, response)
        return self.conversation

    async def delete_conversation(self) -> bool:
        result = await self.conversation_storage.delete_conversation()
        return result
