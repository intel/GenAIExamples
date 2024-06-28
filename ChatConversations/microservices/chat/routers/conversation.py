# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
from logging.config import dictConfig
from typing import Annotated

import pydantic
import requests
import schema.type as type
from conf.config import Settings
from core.common.logger import Logger
from core.service.conversation import ConversationBuilder
from core.util.exception import ConversationApiError
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from schema.payload import (
    ConversationList,
    ConversationModel,
    ConversationModelResponse,
    ConversationRequest,
    UpsertedConversation,
)
from sse_starlette import EventSourceResponse

router = APIRouter()
settings = Settings()
dictConfig(Logger().model_dump())
logger = logging.getLogger(settings.APP_NAME)


@router.get(
    "/conversations",
    tags=["Conversation API"],
    summary="Get current user's all conversations",
)
@router.get("/conversations/", include_in_schema=False)
async def get_all_conversations(
    req: Request,
    user: Annotated[str, Query(description="User")],
) -> type.ConversationServiceResponseWrapper[ConversationList]:
    """Get all conversations for user.

    **Args:**

     - Query Parameters:

            user_id (string): User_ID for which to retrieve conversation.

    **Raises:**

     - 500 Internal Server Error:
        When some error occurs in reading or loading the settings variable as JSON

    Returns:

        JSON Response: (status 200) User's complete list of conversations for a given use_case
    """
    try:
        logger.info("Get conversation for user: {}.".format(user))

        conv_builder = ConversationBuilder(user=user)
        conversations: ConversationList = await conv_builder.get_conversations_for_user()
        response = type.ConversationServiceResponseWrapper(data=conversations)
        return response

    except ConversationApiError as e:
        logger.error(e)
        raise HTTPException(status_code=e.status_code, detail=e.message)

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get(
    "/conversations/{conversation_id}",
    tags=["Conversation API"],
    summary="Get conversation for a specific conversation ID for current user",
)
@router.get("/conversations/{conversation_id}/", include_in_schema=False)
async def get_conversation_by_id(
    req: Request,
    conversation_id: type.MongoObjectId,
    user: Annotated[str, Query(description="User")],
    response: Response,
) -> ConversationModelResponse | None:
    """Get conversation for a given conversation ID.

    **Args:**

     - Path Parameters:

        conversation_id (string): Conversation ID for the required conversation

    **Raises:**

     - 500 Internal Server Error:
        When some error occurs in reading or loading the settings variable as JSON

    **Returns:**

        JSON Response: (status 200) User's conversation for given conversation_id
    """
    try:
        logger.info("Get conversation for id: {}.".format(conversation_id))

        conv_builder = ConversationBuilder(user=user, conversation_id=conversation_id)
        conversation: ConversationModel = await conv_builder.get_existing_conversation()

        if not conversation:
            response.status_code = status.HTTP_404_NOT_FOUND
        else:
            # If conversation is available, parse it as ConversationResponse object to
            # avoid DB attribs in response.
            conversation_dict = conversation.model_dump()
            conversation: ConversationModelResponse = pydantic.parse_obj_as(
                ConversationModelResponse, conversation_dict
            )

        return conversation

    except ConversationApiError as e:
        logger.error(e)
        raise HTTPException(status_code=e.status_code, detail=e.message)

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.delete(
    "/conversations/{conversation_id}",
    tags=["Conversation API"],
    summary="Delete a conversation having a given conversation ID for current user",
    status_code=status.HTTP_204_NO_CONTENT,
)
@router.delete(
    "/conversations/{conversation_id}/",
    include_in_schema=False,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    req: Request,
    conversation_id: type.MongoObjectId,
    user: Annotated[str, Query(description="User")],
    response: Response,
) -> None:
    """Delete conversation with given conversation_id for current user.

    **Args:**

     - Path Parameters

            conversation_id (string): ID of conversation to be deleted.

    **Raises:**

     - 500 Internal Server Error:
        When some error occurs in reading or loading the settings variable as JSON

    **Returns:**

        No Content (status 204): After Successful deletion
    """
    try:
        logger.info("Delete the conversation id :{}".format(conversation_id))
        conv_builder = ConversationBuilder(user=user, conversation_id=conversation_id)
        exists_and_deleted: bool = await conv_builder.delete_conversation()

    except ConversationApiError as e:
        logger.error(e)
        raise HTTPException(status_code=e.status_code, detail=e.message)

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post(
    "/conversations",
    tags=["Conversation API"],
    summary="Initiate a new conversation",
)
@router.post("/conversations/", include_in_schema=False)
async def create_conversation(
    req: Request,
    user: Annotated[str, Query(description="User")],
    payload: ConversationRequest,
) -> UpsertedConversation:
    """API endpoint to start a new conversation.

    **Args:**

     - Body Parameters

            messages (str | JSON): A query string or a list of messages containing "system", "user" and "assistant" key and values.
            temperature (float): (Optional) Temperature param for LLM
            model (string): (Required) LLM to be used for Inference
            max_tokens (int): (Optional) Max token to be generated by LLM,
            stream (bool): (Optional) Flag for whether to stream the LLM response


    **Raises:**

     - 500 Internal Server Error:

            When some error occurs in reading or loading the settings variable as JSON

    **Returns:**

        response (StreamingResponse | JSON): Streamed or non-streamed JSON response based on stream flag in request
            containing the new conversation and its metadata.
    """
    try:
        conversation_builder = ConversationBuilder(
            user=user,
            conversation_request=payload,
        )

        await conversation_builder.initialize_new_conversation()

        if payload.stream:
            result = conversation_builder.stream_and_build_conversation()
            return EventSourceResponse(result, media_type="text/event-stream")
        else:
            conversation: UpsertedConversation = await conversation_builder.build_conversation()
            logger.info(conversation)
            return conversation

    except ConversationApiError as e:
        logger.error(e)
        raise HTTPException(status_code=e.status_code, detail=e.message)

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post(
    "/conversations/{conversation_id}",
    tags=["Conversation API"],
    summary="Resume an existing conversation for current user",
)
@router.post("/conversations/{conversation_id}/", include_in_schema=False)
async def continue_conversation(
    req: Request,
    user: Annotated[str, Query(description="User")],
    payload: ConversationRequest,
    conversation_id: type.MongoObjectId,
) -> UpsertedConversation:
    """API endpoint to resume an exiting conversation.

    **Args:**

     - Body Parameters

            messages (str | JSON): A query string or a list of messages containing "system", "user" and "assistant" key and values.
            temperature (float): (Optional) Temperature param for LLM
            model (string): (Required) LLM to be used for Inference
            max_tokens (int): (Optional) Max token to be generated by LLM,
            stream (bool): (Optional) Flag for whether to stream the LLM response

     - Path Parameters

             conversation_id (string): ID for the conversation to be updated


     **Raises:**
     - 500 Internal Server Error:

            When some error occurs in reading or loading the settings variable as JSON


     **Returns:**

         response (StreamingResponse | JSON): Streamed or non-streamed JSON response based on stream flag in request
             containing the new message and its metadata for the conversation.
    """
    try:
        logger.info("Continue conversation for id: {}".format(conversation_id))
        conversation_builder = ConversationBuilder(
            user=user, conversation_request=payload, conversation_id=conversation_id
        )
        await conversation_builder.continue_existing_conversation()

        if payload.stream:
            result = conversation_builder.stream_and_build_conversation()
            return EventSourceResponse(result, media_type="text/event-stream")
        else:
            conversation = await conversation_builder.build_conversation()
            return conversation
    except ConversationApiError as e:
        logger.error(e)
        raise HTTPException(status_code=e.status_code, detail=e.message)

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
