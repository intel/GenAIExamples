# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
import uuid
from decimal import Decimal
from typing import Annotated, List, Optional, Tuple, TypeAlias

from comps.cores.proto.api_protocol import ChatCompletionRequest
from conf.config import Settings
from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import model_validator
from schema.message import MessageModel
from schema.type import AlphaNumericString, MongoObjectId
from typing_extensions import Self

settings = Settings()


class InferenceMetadata(BaseModel):
    type: str
    model: str


class InferenceSettings(BaseModel):
    model: str | InferenceMetadata = ""
    temperature: Optional[Decimal] = 0.4
    token_limit: Optional[int] = 500
    input_token: Optional[int] = None
    output_token: Optional[int] = None

    model_config = ConfigDict(extra="forbid")


class ConversationRequest(ChatCompletionRequest):

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_messages(self) -> Self:
        """Verify if the messages request parameter is having valid
        values for role key, if the messages parameter is a list of dicts."""

        if not isinstance(self.messages, str):
            for message in self.messages:
                msg_role = message.get("role")
                if msg_role not in ["system", "user", "assistant"]:
                    raise ValueError("Invalid value for messages parameter.")

            # Check if last message in the messages List is actually the user question.
            last_message = self.messages[-1]
            if last_message.get("role") != "user":
                raise ValueError("Invalid format for messages parameter. Last message should be the user query.")

        return self


class ConversationBase(BaseModel):
    conversation_id: Annotated[Optional[MongoObjectId], Field(alias="_id")] = None
    user_id: Optional[AlphaNumericString] = None
    first_query: str
    message_count: int = 0
    created_at: int = int(time.time())
    updated_at: int = int(time.time())
    model_config = ConfigDict(populate_by_name=True)


class ConversationModel(ConversationBase):
    """Model used for dumping conversations into DB stores and
    getting conversations stored in storage."""

    messages: List[MessageModel] = []


class ConversationModelResponse(ConversationModel):
    """Model used for sending complete conversation details as an
    API response.

    This avoids the DB attributes in response.
    """

    conversation_id: Annotated[Optional[MongoObjectId], Field(validation_alias="_id")] = None


class ConversationBaseResponse(ConversationBase):
    """Model used of sending a conversation details without messages, as an
    API response.

    This avoids the DB attributes in response.
    """

    conversation_id: Annotated[Optional[MongoObjectId], Field(validation_alias="_id")] = None


class UpsertedConversation(ConversationBase):
    """Model used for sending as API Response.

    Contains details of
    Updated or or newly inserted conversation. This also help avoid
    DB attributes in API response.
    """

    conversation_id: Optional[MongoObjectId] = None
    last_message: MessageModel


ConversationList: TypeAlias = List[ConversationBaseResponse]
