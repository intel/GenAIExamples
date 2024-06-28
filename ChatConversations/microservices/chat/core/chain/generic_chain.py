# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
from logging.config import dictConfig
from typing import Any

from conf.config import Settings
from core.common.logger import Logger
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

settings = Settings()
dictConfig(Logger().model_dump())
logger = logging.getLogger(settings.APP_NAME)


class GenericChain:
    model_params: dict[str, Any]
    prompt_with_user_context: str
    context: bool

    def __init__(
        self,
        retriever_params: dict = None,
        temp: float = 0.4,
        token_limit: int = 500,
        context: bool = False,
        stream: bool = False,
        callbacks=[],
    ):
        # Check if prepare_prompt method is called by base classes or not.
        if not hasattr(self, "prompt_without_context") and not hasattr(self, "prompt_with_context"):
            raise Exception("Prompt is not set. Can not build chain.")

        self.temperature = temp
        self.token_limit = token_limit
        self.use_retriever = False
        self.context = context
        self.stream = stream
        self.callbacks = callbacks
        self.model_params = {
            "max_tokens": token_limit,
            "temperature": temp,
            "streaming": stream,
            "callbacks": callbacks,
        }
        self.retriever_params = retriever_params

    def get_llm(self):
        raise NotImplementedError

    def get_non_streaming_llm(self):
        raise NotImplementedError

    def get_retriever(self):
        raise NotImplementedError

    def get_num_tokens(self, messages=""):
        raise NotImplementedError

    def set_use_retriever(self, val):
        self.use_retriever = val

    def prepare_prompt(self):
        # Get and store each type of prompts from prompts store dict.
        self.prompt_with_context = """\n\nHuman: You are a helpful AI Assistant.
        Answer questions by considering following context:
        {context}
        Answer the following question: {question}

        \n\nAssistant:
        """

        self.prompt_with_user_context = """You are a helpful AI Assistant which is great a answering questions based on provided context.
        Answer questions by considering following context:

        {context}

        Question: {question}
        """

        self.prompt_without_context = """\n\nHuman: You are a helpful AI Assistant.
        Answer questions by considering following context:
        {chat_history}
        This is the Question from the user: {question}

        \n\nAssistant:
        """

    def build_chain_without_retriever(self):

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                MessagesPlaceholder("messages"),
            ]
        )

        chain = prompt | self.get_llm()
        return chain

    async def build_chain(self):
        return self.build_chain_without_retriever()
