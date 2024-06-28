# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from conf.config import Settings
from fastapi import APIRouter

router = APIRouter()
settings = Settings()


@router.get("/health", tags=["Status API"], summary="Check API health status")
@router.get("/health/", include_in_schema=False)
async def health():
    """Checks the availability status of Conversation Manager APIs.

    **Response**:

    - **status** (string): A string describing health status.
    """
    return {"status": "healthy"}
