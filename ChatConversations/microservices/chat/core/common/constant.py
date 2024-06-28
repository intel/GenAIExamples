# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class Literals:
    conversations = "conversations"
    tags = "tags"
    projects = "projects"
    feedbacks = "feedbacks"


class Prompt:
    system = """You are a helpful AI Assistant. You answer all questions in brief \
and concise manner. You don't answer in more than 5 sentences. When asked for details, \
you answer in a very detailed fashion but still not more than 12 sentences. You refuse \
to answer offensive and inappropriate answer. You don't try to answer the questions you \
don't know."""


class Message:
    class Error:
        INVALID_IMPLEMENTATION = "Something is wrong with implementation logic."
        METHOD_NOT_ALLOWED = (
            "The requested API endpoint does not support the authorization flow being used by the client application."
        )
        GATEWAY_ERROR = "Some error occurred at Model Service Provider."
        MODEL_LIMIT_REACHED = "Selected Model is temporarily overloaded as there are too many active users. Please use a different model or retry after some time."
        RETRIEVER_SERVICE_THROTTLING = "Retriever service is temporarily overloaded. Please retry after some time."
        RETRIEVER_PROVIDER_ERROR = (
            "Retriever service is currently unavailable or failing to respond. Please retry after some time."
        )
        OPENAI_KEY_MISSING = "OPENAI_API_KEY and OPENAI_API_BASE not set."
        KEY_NOT_FOUND_ERROR = "Key Not Found Error"
        VALUE_NOT_FOUND_ERROR = "Value Not Found Error"
        ROLE_NOT_FOUND = "Provided Role is not valid."
        USECASE_NOT_FOUND = "Provided use case was not found."
        INDEX_NOT_FOUND = "Provided Index Name was not found."
        PROMPT_NOT_FOUND = "Provided Prompt was not found."
        EXCEED_CONTEXT_LIMIT = "Maximum context limit reached, please reduce the length of the content."

        INVALID_CONVERSATION_ID = "Conversation ID is invalid."
        INVALID_MESSAGE_ID = "Message ID is invalid"
        INVALID_TAG_ID = "Invalid tag ID. Perhaps the fetched tag record does not exist anymore."
        FACTORY_PATTERN_ERROR = "Error occurred while instantiating classes using factory."
        MAX_MESSAGES_LIMIT_EXCEEDED = (
            "Limit for Maximum Messages for this Conversation Exceeded. Please start a New Conversation."
        )
        MAX_CONVERSATION_LIMIT_EXCEEDED = (
            "Limit for Maximum Conversations Exceeded. Please delete an existing Conversation."
        )
        INVALID_TOKEN_LIMIT = "Invalid token_limit value for selected model."

        SYNC_FAILED = "Sync process failed due to some error."
        STREAMING_ERROR = "Error: Answer could not be generated due to some internal error!"
        PRESIGNED_URL_ERROR = "Error: Could not fetch presigned URL."
        UNSUPPORTED_IMAGE_TYPE = "The image file format you've uploaded is not supported. Ensure to only upload images in jpeg, png, or gif formats."
        UNSUPPORTED_MODEL_FEATURE = "The feature is not supported by the provided model."
        MAX_IMAGE_SIZE_EXCEEDED = "Given image exceeds 3MB size limit."

        MISSING_MESSAGE_UPDATE_DATA = "Request body should have either assistant or feedback values set."

        INVALID_WIKI_URL = "Provided WIKI URL is invalid"

    class Warning:
        CACHE_PUT_FAILED = "Could not cache the requested item."
        NON_EXISTENT_CACHE_KEY = "Trying to set a non-existent key for cache."
        CACHE_BUSTING_FAILED = "Failed to invalidate the cache key."
        FEEDBACK_DOC_USE_CASE_MISSING = "Project Name (Use Case) not provided. Proceeding, however, feedback report will not be having project name."
        FEEDBACK_REPORT_FAILED = "Failed to update feedback report in storage. Proceeding."

    class Plugin:
        INVALID_MANIFEST = "Invalid plugin manifest file."
        INVALID_PLUGIN_MODULE = "Could not import plugin module mentioned in manifest file."
        ENV_NOT_SET = "Required environment variable is not set."
        INVALID_PLUGIN_CLASS = "Could not find plugin class provided in manifest file."
        ALREADY_REGISTERED = "Plugin is already registered. Please check your manifest file for duplicate entries."

        class Llm:
            UNREGISTERED_LLM = "No registered llm object found for provided model name."
            MODEL_NOT_PROVIDED = "No model type was provided."
            INVALID_ATTRIBUTE_NAME = "Attribute name not found for the given model."
            INVALID_TEMP = "Invalid value for temperature for the given model."
            INVALID_TOKEN_LIMIT = "Invalid value for token limit for the given model."

        class Retriever:
            UNREGISTERED_RETRIEVER = "No registered retriever/sync-controller found for provided index type."
            INDEX_NOT_PROVIDED = "No index type was provided."
            INVALID_RETRIEVER = "Provided retriever is not valid."

    class DB:
        NEW_TABLE_ERROR = "Error occurred while creating new table."
        EXISTING_TABLE_ERROR = "Table for an existing user doesn't seem to exist."
        TABLE_DOESNOT_EXIST = "Table does not exist."
        COLLECTION_NAME_ERROR = "Could not get the required Collection name. Did you forget to update collections dict?"
        MESSAGE_UPDATE_ERROR = "An error occurred while updating message!"
        MESSAGE_FETCH_ERROR = "Could not fetch message using the Message ID!"

    class Conversation:
        STORAGE_NOT_SET = "Conversation storage must be set before creating conversation."
        CONVERSATION_NOT_FOUND = "Required conversation was not found."
        CONVERSATION_ID_NOT_SET = "Conversation ID is not set. Can not proceed."
        MESSAGE_ID_NOT_SET = "Message ID is not set. Can not proceed."
        MSG_UPDATE_DATA_NOT_SET = "At least one value required to update the message is not set."
        USE_CASE_NOT_SET = "use_case is not set"
        NO_EXISTING_CONVERSATION = "No existing conversation found for user."
        TITLE_NOT_SET = "Conversation title cannot be empty"
        TITLE_SPACES_ONLY = "Title cannot contain only spaces"
        TITLE_MIN_LEN = "Title must be at least 3 characters long"
        TITLE_UNIQUE = "Conversation title should be unique"

    class File_Error:
        EMPTY_FILE = "Uploaded file is empty. Please check the file and try again"
