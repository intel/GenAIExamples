# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import re
from typing import Annotated, Generic, TypeAlias, TypeVar

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict

alpha_numperic_pattern: str = r"^[a-zA-Z_0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9_]$"


def validate_alpha_num_extended(val: str):
    match = re.match(alpha_numperic_pattern, val)
    assert match is not None, "Invalid or unsupported value."
    return val


AlphaNumericString: TypeAlias = Annotated[str, AfterValidator(validate_alpha_num_extended)]

MongoObjectId: TypeAlias = Annotated[str, BeforeValidator(str)]

# Generic template for API response wrapper
T = TypeVar("T")


class ConversationServiceResponseWrapper(BaseModel, Generic[T]):
    data: T

    model_config = ConfigDict(extra="forbid")
