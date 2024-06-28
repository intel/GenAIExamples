# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
from logging.config import dictConfig

from conf.config import Settings
from core.chain.generic_chain import GenericChain
from core.chat_model.llm_factory import LlmFactory
from core.common.logger import Logger
from langchain.callbacks.base import BaseCallbackHandler

settings = Settings()
dictConfig(Logger().model_dump())
logger = logging.getLogger(settings.APP_NAME)


class OpenaiChain(GenericChain):
    model_type: str
    callbacks: list[BaseCallbackHandler]

    def __init__(
        self,
        model: str,
        retriever_params: dict = None,
        temp: float = 0.4,
        token_limit: int = 500,
        context: bool = False,
        stream: bool = False,
        callbacks=BaseCallbackHandler(),
    ):
        self.model_type = model
        self.prepare_prompt()
        super().__init__(retriever_params, temp, token_limit, context, stream, callbacks)

    def get_llm(self):
        return LlmFactory.create(self.model_type).instantiate_llm(self.model_params)

    def get_non_streaming_llm(self):
        self.model_params["streaming"] = False
        return LlmFactory.create(self.model_type).instantiate_llm(self.model_params)

    def get_num_tokens(self, messages=""):
        llm = self.get_llm()
        return llm.get_num_tokens(messages)

    # Override this function to provide a custom prompt for OpenAI Models
    def prepare_prompt(self):
        super().prepare_prompt()
