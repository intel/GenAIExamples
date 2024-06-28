# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Any

from core.chat_model.llm_interface import LlmInterface
from langchain_community.chat_models import ChatOpenAI


@dataclass
class CustomModel(LlmInterface):
    api_base: str
    api_key: str = "EMPTY"

    def instantiate_llm(self, params: dict[str, Any]) -> Any:
        temp = params.get("temperature", self.temperature)
        max_tokens = params.get("max_tokens", self.token_limit)
        streaming = params.get("streaming", False)
        callbacks = params.get("callbacks", [])

        model_kwargs = {
            "model_name": self.model_name,
            "openai_api_base": self.api_base,
            "openai_api_key": self.api_key,
            "streaming": streaming,
            "temperature": temp,
            "max_tokens": max_tokens,
            "callbacks": callbacks,
        }

        return ChatOpenAI(**model_kwargs)
