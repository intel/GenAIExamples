# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM node as vite-app

WORKDIR /usr/app
COPY . /usr/app

ARG VITE_SERVICE_URL
ENV VITE_SERVICE_URL=$VITE_SERVICE_URL


RUN ["npm", "install"]
RUN ["npm", "run", "build"]


FROM nginx:alpine
EXPOSE 80


COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=vite-app ./usr/app/dist /usr/share/nginx/html

ENTRYPOINT ["nginx", "-g", "daemon off;"]