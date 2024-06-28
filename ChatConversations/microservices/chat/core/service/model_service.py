# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from logging.config import dictConfig
from typing import Any

import pydantic
import schema.model as schema
from conf.config import Settings
from core.common.constant import Message
from core.common.logger import Logger
from core.util.exception import ConversationManagerError

settings = Settings()
dictConfig(Logger().model_dump())
logger = logging.getLogger(settings.APP_NAME)


class SupportedModels:
    @staticmethod
    async def get_model_attribute(model_type: str, attribute_name: str, user_id: str) -> str:
        attribute_value: Any = ""
        model_list: schema.ModelList = await SupportedModels.get_all_models(user_id)
        result = [getattr(model, attribute_name, "") for model in model_list if model.model_type == model_type]

        attribute_value = result[0] if result else ""

        if not attribute_value:
            logger.warn(Message.Plugin.Llm.INVALID_ATTRIBUTE_NAME)

        return attribute_value

    @staticmethod
    async def get_all_models(user_id: str) -> schema.ModelList:
        """Get list of all registered models and their properties."""

        model_list: schema.ModelList = []
        with open(settings.PLUGIN_FILE, "r") as model_file:
            try:
                plugin_data = json.load(model_file)
                # Get list of all enabled and non-restricted llms
                enabled_llms = [
                    plugin
                    for plugin in plugin_data
                    if not plugin.get("disabled", False)
                    and not plugin.get("restricted", False)
                    and plugin.get("plugin_type") == "llm"
                ]

                for data in enabled_llms:
                    # Initialize a dict with all args of current_model except model_name.
                    # model_name is not required to be exposed as API responses.
                    args = data.get("args", {})
                    model_props = dict((k, v) for k, v in args.items() if k != "model_name")

                    # Update the dict with props fields from manifest file.
                    model_props.update(data.get("props"))

                    # Prepare the model_list by inserting all the above model details.
                    model = pydantic.parse_obj_as(schema.ModelMetadata, model_props)
                    model_list.append(model)

            except (KeyError, ValueError) as e:
                logger.error(f"{Message.Plugin.INVALID_MANIFEST} Error: {e}")
                raise ConversationManagerError()

        return model_list
