#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

IMAGE_REPO=${IMAGE_REPO:-$OPEA_IMAGE_REPO}
IMAGE_TAG=${IMAGE_TAG:-latest}

function getImagenameFromMega() {
    echo $(echo "$1" | tr '[:upper:]' '[:lower:]')
}

function checkExist() {
    IMAGE_NAME=$1
    if [ $(curl -X GET http://localhost:5000/v2/opea/${IMAGE_NAME}/tags/list | grep -c ${IMAGE_TAG}) -ne 0 ]; then
        echo "true"
    else
        echo "false"
    fi
}

function docker_build() {
    # check if if IMAGE_TAG is not "latest" and the image exists in the registry
    if [ "$IMAGE_TAG" != "latest" ] && [ "$(checkExist $1)" == "true" ]; then
        echo "Image ${IMAGE_REPO}opea/$1:$IMAGE_TAG already exists in the registry"
        return
    fi
    # docker_build <service_name> <dockerfile>
    if [ -z "$2" ]; then
        DOCKERFILE_PATH=Dockerfile
    else
        DOCKERFILE_PATH=$2
    fi
    echo "Building ${IMAGE_REPO}opea/$1:$IMAGE_TAG using Dockerfile $DOCKERFILE_PATH"
    # if https_proxy and http_proxy are set, pass them to docker build
    if [ -z "$https_proxy" ]; then
        docker build --no-cache -t ${IMAGE_REPO}opea/$1:$IMAGE_TAG -f $DOCKERFILE_PATH .
    else
        docker build --no-cache -t ${IMAGE_REPO}opea/$1:$IMAGE_TAG --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f $DOCKERFILE_PATH .
    fi
    docker push ${IMAGE_REPO}opea/$1:$IMAGE_TAG
    docker rmi ${IMAGE_REPO}opea/$1:$IMAGE_TAG
}

# $1 is like "apple orange pear"
for MEGA_SVC in $1; do
    case $MEGA_SVC in
        "ChatQnA"|"CodeGen"|"CodeTrans"|"DocSum"|"Translation")
            cd $MEGA_SVC/docker
            IMAGE_NAME="$(getImagenameFromMega $MEGA_SVC)"
            docker_build ${IMAGE_NAME}
            cd ui
            docker_build ${IMAGE_NAME}-ui docker/Dockerfile
            if [ "$MEGA_SVC" == "ChatQnA" ];then
                docker_build ${IMAGE_NAME}-conversation-ui docker/Dockerfile.react
            fi
            ;;
        "AudioQnA"|"SearchQnA"|"VisualQnA")
            echo "Not supported yet"
            ;;
        *)
            echo "Unknown function: $MEGA_SVC"
            ;;
    esac
done
