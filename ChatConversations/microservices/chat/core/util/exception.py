# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from core.common.constant import Message
from fastapi import status
from fastapi.responses import JSONResponse


def get_formatted_error(req, exc):
    error_json = {"error": {"code": exc.status_code, "message": exc.detail}}
    return JSONResponse(content=error_json, status_code=exc.status_code)


class ConversationApiError(Exception):
    """Base Class for custom exception classes."""

    def __init__(
        self,
        message=" Conversation Manager API Error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ConversationManagerError(ConversationApiError):
    """Custom Exception to show Internal Server Error at  Conversation Manager."""

    def __init__(
        self,
        message="Some error occurred at  Conversation Manager.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message, self.status_code)


class ThrottlingError(ConversationApiError):
    """Custom exception to be raised when LLMs are causing throttling errors."""

    def __init__(
        self,
        message=Message.Error.MODEL_LIMIT_REACHED,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    ):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message, self.status_code)


class ModelServerError(ConversationApiError):
    """Custom exception to be raised when some error occurs at LLM Servers."""

    def __init__(
        self,
        message=Message.Error.GATEWAY_ERROR,
        status_code=status.HTTP_502_BAD_GATEWAY,
    ):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message, self.status_code)


class RetrieverProviderError(ConversationApiError):
    """Custom exception to be raised when some error occurs while using Retriever services."""

    def __init__(
        self,
        message=Message.Error.RETRIEVER_PROVIDER_ERROR,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    ):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message, self.status_code)


class ResourceNotFoundError(ConversationApiError):
    """Custom Exception to show Internal Server Error at  Conversation Manager."""

    def __init__(
        self,
        message="Requested resource was not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    ):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message, self.status_code)


class ValidationError(ConversationApiError):
    """Custom Exception to show Validation Error Conversation Manager."""

    def __init__(
        self,
        message="Invalid Request.",
        status_code=status.HTTP_400_BAD_REQUEST,
    ):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message, self.status_code)


class AuthorizationError(ConversationApiError):
    """Custom Exception to authorization error in Conversation Manager."""

    def __init__(self, message="Authorization failed.", status_code=status.HTTP_401_UNAUTHORIZED):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message, self.status_code)


class InvalidRequestFile(ConversationApiError):
    """Custom Exception for invalid request file."""

    def __init__(
        self,
        message="The file you have uploaded is either invalid or corrupted. \
        Please check the file and try again.",
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    ):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message, self.status_code)
