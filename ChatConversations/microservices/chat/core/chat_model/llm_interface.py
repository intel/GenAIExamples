# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from core.plugin import PluginFactory


@dataclass
class LlmInterface(ABC):
    model_type: str
    model_name: str
    token_limit: int
    temperature: float

    @abstractmethod
    def instantiate_llm(self, params: dict) -> Any:
        """Instantiate and return the relevant llm."""
        pass

    def register_plugin(self, llm_factory: PluginFactory) -> None:
        """Register the current class with its model type."""

        # Register the current llm object mapped to unique model type
        llm_factory.register(self.model_type, self)
