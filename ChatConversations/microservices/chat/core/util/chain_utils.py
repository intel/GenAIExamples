# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from logging.config import dictConfig
from typing import Any, Dict, List

import openai
from conf.config import Settings
from core.chain.generic_chain import GenericChain
from core.chain.openai_chain import OpenaiChain
from core.common.constant import Message, Prompt
from core.common.logger import Logger
from core.service.model_service import SupportedModels
from core.util.exception import ConversationApiError, ConversationManagerError, ModelServerError, ThrottlingError
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain.schema import LLMResult
from schema.payload import ConversationRequest

settings = Settings()
dictConfig(Logger().model_dump())
logger = logging.getLogger(settings.APP_NAME)


class AsyncFinalIteratorCallbackHandler(AsyncIteratorCallbackHandler):
    """Inherits a callback handler that returns an async iterator.

    Only the final output of the chain will be iterated and streamed.
    """

    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        # Reset streaming flags
        self.done.clear()

        # Set initial value to false when LLM starts answering.
        self.is_final_answer = False

    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        # When LLM stops answering, stop streaming event only when it is final answer from the
        # LLM (i.e. it should not be intermediate answers like condensed question generation.)
        if self.is_final_answer:
            self.done.set()

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        # This method is called only for LLM calls having streaming enabled. As we
        # enter here, we set the final answer flag to True. By design, we will use
        # streaming LLM only for final answer, not for intermediate answers.
        self.is_final_answer = True

        # If we get streaming token, we keep populating the queue. Async iteration on this
        # queue is handled by base class.
        if token:
            self.queue.put_nowait(token)


class GetPromptCallbackHandler(BaseCallbackHandler):
    """Inherits a callback handler that returns formatted prompt that being parse into LLM."""

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> Any:
        # Concatenates the list of prompts into a string.
        # Inserting newline separator between each elements in the list.
        self.formatted_prompts = "\n".join(prompts)


class ChainFactory:
    # TODO
    """Change the following instantitation pattern to new Factory-registration pattern.

    instantiate_chain static method should be able to instantiate different types
    of chain classes based on model or type of chain required.
    """

    @staticmethod
    async def get_conversation_chain(
        user: str,
        req: ConversationRequest,
        stream: bool = False,
        callbacks: list[BaseCallbackHandler] = [],
    ) -> GenericChain:
        model: str = req.model
        temperature: float = float(req.temperature)
        token_limit: int = req.max_tokens

        chain_params = {
            "model": model,
            "temp": temperature,
            "token_limit": token_limit,
            "stream": stream,
            "callbacks": callbacks,
        }

        # TO BE IMPROVED when pluggable chain module task is taken
        model_platform = await SupportedModels.get_model_attribute(model, "platform", user)

        try:
            # TODO
            # This pattern to be fixed in new design pattern updates
            if model_platform in ["azure", "edge", "ray"]:
                chain = OpenaiChain(**chain_params)

            else:
                logger.error(Message.Plugin.Llm.UNREGISTERED_LLM)
                raise ConversationManagerError()

            return chain

        except NotImplementedError:
            raise NotImplementedError
        except Exception as e:
            logger.error(e)
            raise ConversationManagerError()


class ChainHelper:
    @staticmethod
    async def build_execute_chain(
        user: str,
        conversation: ConversationRequest,
        system_prompt: str,
        user_prompt: list[tuple],
        stream: bool = False,
        callbacks: list[BaseCallbackHandler] = [],
    ) -> dict:
        try:
            result = {}
            chain_obj = await ChainFactory.get_conversation_chain(
                user, conversation, stream=stream, callbacks=callbacks
            )
            chain = await chain_obj.build_chain()

            input = {"system_prompt": system_prompt or Prompt.system, "messages": user_prompt}

            ai_message, llm_input_prompts = await ChainHelper.invoke_chain(chain, input)
            logger.info(llm_input_prompts)

            # Get token count for input prompts
            input_token = chain_obj.get_num_tokens(llm_input_prompts)

            # Get token count for output response
            answer = ai_message.content
            output_token = chain_obj.get_num_tokens(answer)

            # Include input_token and output_token into result dict()
            result["answer"] = answer
            result["input_token"] = input_token
            result["output_token"] = output_token

            logger.info(result)

            return result

        except ConversationApiError as e:
            raise e

        except Exception as e:
            logger.error(e)
            raise ConversationManagerError()

    @staticmethod
    async def invoke_chain(chain, chain_input, chain_params={}):
        prompt_handler = GetPromptCallbackHandler()

        try:
            config = {"callbacks": [prompt_handler]}

            result = await chain.ainvoke(chain_input, **chain_params, config=config)
            llm_prompts = prompt_handler.formatted_prompts

        # Handle some specified errors from openai API
        except openai.RateLimitError as e:
            logger.error(e)
            raise ThrottlingError()

        except ValueError as e:
            logger.error(e)
            if "ThrottlingException" in str(e) or "ModelTimeoutException" in str(e):
                raise ThrottlingError()
            else:
                raise ModelServerError()

        # Handle the unhandled openai errors and other unexpected errors
        except Exception as e:
            logger.error(e)
            raise ModelServerError()

        return result, llm_prompts
