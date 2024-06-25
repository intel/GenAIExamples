from abc import ABC, abstractmethod
from dataclasses import dataclass
from core.plugin import PluginFactory
from typing import Any


@dataclass
class LlmInterface(ABC):
    model_type: str
    model_name: str
    token_limit: int
    temperature: float

    @abstractmethod
    def instantiate_llm(self, params: dict) -> Any:
        """Instantiate and return the relevant llm"""
        pass

    def register_plugin(self, llm_factory: PluginFactory) -> None:
        """Register the current class with its model type."""

        # Register the current llm object mapped to unique model type
        llm_factory.register(self.model_type, self)
