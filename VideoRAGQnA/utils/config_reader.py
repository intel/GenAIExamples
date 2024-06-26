# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import yaml


def read_config(path):
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    return config
