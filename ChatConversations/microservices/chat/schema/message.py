# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
import uuid
from decimal import Decimal
from typing import Annotated, List, Optional

from core.common.constant import Message
from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator
from schema.type import AlphaNumericString


# Adding schema for legacy inference entries in database
class InferenceMetadata(BaseModel):
    type: str
    model: str


class InferenceSettings(BaseModel):
    model: str | InferenceMetadata = ""
    temperature: Optional[Decimal] = 0.4
    token_limit: Optional[int] = 500
    input_token: Optional[int] = None
    output_token: Optional[int] = None
    tags: Optional[List[str]] = None

    model_config = ConfigDict(extra="forbid")


class FeedbackModel(BaseModel):
    comment: Optional[str] = ""
    rating: Annotated[Optional[int], Field(ge=0, le=5)] = None
    is_thumbs_up: bool

    model_config = ConfigDict(extra="forbid")


class MessageModel(BaseModel):
    message_id: uuid.UUID
    human: str
    assistant: str = ""
    inference_settings: Optional[InferenceSettings] = None
    feedback: Optional[FeedbackModel] = None
    created_at: int = int(time.time())
    updated_at: int = int(time.time())

    @field_serializer("message_id")
    def serialize_id(self, message_id: uuid.UUID):
        return message_id.hex


class MessageUpdateModel(BaseModel):
    assistant: Optional[str] = None
    feedback: Optional[FeedbackModel] = None

    # use_case param needed for storing it in feedback table after updating the feedback for
    # the message. Its value is not verified for now, and can be any invalid value.
    use_case: Optional[AlphaNumericString] = None

    model_config = ConfigDict(extra="forbid")

    # Validating as per current requirement: Only assistant answer and feedback
    # are to be updated right now.
    @model_validator(mode="after")
    def verify_message_update_payload(self):
        if not self.assistant and not self.feedback:
            raise ValueError(Message.Error.MISSING_MESSAGE_UPDATE_DATA)
        return self
