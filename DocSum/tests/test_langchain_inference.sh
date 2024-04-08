#!/bin/bash
# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
set -xe

function test_env_setup() {
    WORKPATH=$(dirname "$PWD")
    LOG_PATH="$WORKPATH/tests/langchain.log"

    DOCUMENT_SUMMARY_CONTAINER_NAME="test-document-summary"
    DOCSUM_CONTAINER_NAME="test-DocSum_server"
    cd $WORKPATH # go to ChatQnA
}

function rename() {
    # Rename the container names
    cd ${WORKPATH}
    sed -i "s/DocSum_server/${DOCSUM_CONTAINER_NAME}/g" serving/tgi_gaudi/launch_tgi_service.sh
}

function docker_setup() {
    local card_num=1
    local port=8888
    local model_name="Intel/neural-chat-7b-v3-3"

    cd ${WORKPATH}

    # Reset the tgi port
    sed -i "s/8080/$port/g" langchain/docker/summarize-app/app/server.py
    sed -i "s/8080/$port/g" langchain/docker/summarize-app/Dockerfile

    docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
    bash serving/tgi_gaudi/launch_tgi_service.sh $card_num $port $model_name
    sleep 3m # Waits 3 minutes
}

function launch_document_summary_docker() {
    cd $WORKPATH
    local port=8890
    sed -i "s/port=8000/port=$port/g" langchain/docker/summarize-app/app/server.py

    docker run -d --net=host --ipc=host \
        --name=$DOCUMENT_SUMMARY_CONTAINER_NAME \
        -v /var/run/docker.sock:/var/run/docker.sock intel/gen-ai-examples:document-summarize bash
}

function launch_server() {
    cd $WORKPATH

    # Start the Backend Service
    docker exec $DOCUMENT_SUMMARY_CONTAINER_NAME \
        bash -c "export HUGGINGFACEHUB_API_TOKEN=$HUGGING_FACE_TOKEN;nohup python server.py &"
    sleep 1m
}

function run_tests() {
    cd $WORKPATH
    local port=8890
}

function check_response() {
    cd $WORKPATH
    echo "Checking response"
    local status=false
    if [[ $(grep -c "\$51.2 billion" $LOG_PATH) != 0 ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed"
        exit 1
    else
        echo "Response check succeed"
    fi
}

function docker_stop() {
    local container_name=$1
    cid=$(docker ps -aq --filter "name=$container_name")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid; fi
}

function main() {
    test_env_setup
    rename
    docker_stop $DOCSUM_CONTAINER_NAME && docker_stop $DOCUMENT_SUMMARY_CONTAINER_NAME

    docker_setup
    launch_document_summary_docker
    launch_server

    run_tests

    docker_stop $DOCSUM_CONTAINER_NAME && docker_stop $DOCUMENT_SUMMARY_CONTAINER_NAME
    echo y | docker system prune

    check_response
}

main
