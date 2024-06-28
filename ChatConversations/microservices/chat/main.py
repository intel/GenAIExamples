# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import uvicorn
from conf.config import Settings
from core.util.exception import get_formatted_error
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from plugin_loader import PluginLoader
from routers import conversation, health

settings = Settings()
app = FastAPI(
    title=settings.APP_DISPLAY_NAME,
    description="Conversation API for interacting with LLMs with database",
    redoc_url="/",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(conversation.router)

PluginLoader.load_modules()


# Setting a custom HTTPException Handler which returns formatted error response
@app.exception_handler(HTTPException)
async def pipeline_api_http_exception_handler(request, exc):
    return get_formatted_error(request, exc)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_DNS,
        port=settings.APP_PORT,
        reload=True,
    )
