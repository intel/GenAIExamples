# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Use Alpine-based Python image
FROM python:3.10-alpine3.18 as build

WORKDIR /chat

# Copy the requirements file into the container.
COPY microservices/chat/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY microservices/chat .

ENTRYPOINT ["python3","main.py"]