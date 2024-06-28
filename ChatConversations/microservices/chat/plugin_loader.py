# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import importlib
import json
import logging
import os
from logging.config import dictConfig
from typing import Any

import core.factory_names as factory
from conf.config import Settings
from core.common.constant import Message
from core.common.logger import Logger
from core.plugin import Plugin, PluginFactory
from core.util.exception import ConversationManagerError

settings = Settings()
dictConfig(Logger().model_dump())
logger = logging.getLogger(settings.APP_NAME)


class PluginLoader:
    plugin_file: str = settings.PLUGIN_FILE
    super_factory: dict[str, PluginFactory] = {}

    @staticmethod
    def register_plugin_factory(plugin_type: str, plugin_factory: PluginFactory) -> None:
        PluginLoader.super_factory[plugin_type] = plugin_factory

    @staticmethod
    def load_modules():
        """Read llm manifest file.

        load and register all declared modules.
        """

        # Load Plugin modules
        with open(PluginLoader.plugin_file, "r") as plugin_manifest:
            try:
                plugin_specs = json.load(plugin_manifest)
                active_plugin_specs = [plugin for plugin in plugin_specs if not plugin.get("disabled")]

                logger.info("Loading and registering all defined plugin modules.")
                for plugin_data in active_plugin_specs:
                    plugin: Plugin = PluginLoader.import_initialize_module(plugin_data)
                    plugin_factory: PluginFactory = PluginLoader.super_factory.get(plugin_data["plugin_type"])
                    plugin.register_plugin(plugin_factory)

            except ValueError as e:
                logger.error(f"{Message.Plugin.INVALID_MANIFEST} Error: {e}")
                raise ConversationManagerError()

    @staticmethod
    def get_module_envs(envs: dict) -> dict:
        """Get the envs dict from manifest.

        Values in this dict are
        environment variables on host. Load their values in a new dict
        """

        try:
            env_args = dict((key, os.environ[val]) for key, val in envs.items())
            return env_args
        except KeyError as e:
            logger.error(f"{Message.Plugin.ENV_NOT_SET} {e}")
            raise ConversationManagerError(Message.Plugin.ENV_NOT_SET)

    @staticmethod
    def import_initialize_module(data: dict) -> Any:
        try:
            # Import the module mentioned in llm manifest's current entry.
            module = importlib.import_module(data["module"])

            # Get the llm class from attribute list of imported module.
            _class = getattr(module, data["class"])

            # Load the environment variables, if any, from manifest.
            env_args = PluginLoader.get_module_envs(data.get("envs", {}))

            # Return the llm object instantiated with args and envs from manifest.
            return _class(**data["args"], **env_args)

        except (ModuleNotFoundError, ImportError) as e:
            logger.error(f"{Message.Plugin.INVALID_PLUGIN_MODULE} Error: {e}")
            raise ConversationManagerError()

        except AttributeError as e:
            logger.error(f"{Message.Plugin.INVALID_PLUGIN_CLASS} Error: {e}")
            raise ConversationManagerError()

        except (KeyError, ValueError) as e:
            logger.error(e)
            raise ConversationManagerError()


PluginLoader.register_plugin_factory("llm", factory.LlmFactory())
