#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps

    docker build -t opea/whisper:latest  -f comps/asr/whisper/Dockerfile_hpu .

    docker build -t opea/asr:latest  -f comps/asr/Dockerfile .
    docker build -t opea/llm-tgi:latest -f comps/llms/text-generation/tgi/Dockerfile .
    docker build -t opea/speecht5:latest  -f comps/tts/speecht5/Dockerfile_hpu .
    docker build -t opea/tts:latest  -f comps/tts/Dockerfile .

    docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1

    cd ..

    cd $WORKPATH/docker
    docker build --no-cache -t opea/audioqna:latest -f Dockerfile .

    # cd $WORKPATH/docker/ui
    # docker build --no-cache -t opea/audioqna-ui:latest -f docker/Dockerfile .

    docker images
}

function start_services() {
    cd $WORKPATH/docker/gaudi
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

    export TGI_LLM_ENDPOINT=http://$ip_address:3006
    export LLM_MODEL_ID=Intel/neural-chat-7b-v3-3

    export ASR_ENDPOINT=http://$ip_address:7066
    export TTS_ENDPOINT=http://$ip_address:7055

    export MEGA_SERVICE_HOST_IP=${ip_address}
    export ASR_SERVICE_HOST_IP=${ip_address}
    export TTS_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}

    export ASR_SERVICE_PORT=3001
    export TTS_SERVICE_PORT=3002
    export LLM_SERVICE_PORT=3007

    # sed -i "s/backend_address/$ip_address/g" $WORKPATH/docker/ui/svelte/.env

    # Replace the container name with a test-specific name
    # echo "using image repository $IMAGE_REPO and image tag $IMAGE_TAG"
    # sed -i "s#image: opea/chatqna:latest#image: opea/chatqna:${IMAGE_TAG}#g" docker_compose.yaml
    # sed -i "s#image: opea/chatqna-ui:latest#image: opea/chatqna-ui:${IMAGE_TAG}#g" docker_compose.yaml
    # sed -i "s#image: opea/*#image: ${IMAGE_REPO}opea/#g" docker_compose.yaml
    # Start Docker Containers
    docker compose -f docker_compose.yaml up -d
    # n=0
    # until [[ "$n" -ge 200 ]]; do
    #     docker logs tgi-gaudi-server > tgi_service_start.log
    #     if grep -q Connected tgi_service_start.log; then
    #         break
    #     fi
    #     sleep 1s
    #     n=$((n+1))
    # done
    sleep 8m
}


function validate_megaservice() {
    result=$(http_proxy="" curl http://${ip_address}:3008/v1/audioqna -XPOST -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64}' -H 'Content-Type: application/json')
    if [[ $result == *"AAA"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        exit 1
    fi

}

#function validate_frontend() {
#    cd $WORKPATH/docker/ui/svelte
#    local conda_env_name="OPEA_e2e"
#    export PATH=${HOME}/miniforge3/bin/:$PATH
##    conda remove -n ${conda_env_name} --all -y
##    conda create -n ${conda_env_name} python=3.12 -y
#    source activate ${conda_env_name}
#
#    sed -i "s/localhost/$ip_address/g" playwright.config.ts
#
##    conda install -c conda-forge nodejs -y
#    npm install && npm ci && npx playwright install --with-deps
#    node -v && npm -v && pip list
#
#    exit_status=0
#    npx playwright test || exit_status=$?
#
#    if [ $exit_status -ne 0 ]; then
#        echo "[TEST INFO]: ---------frontend test failed---------"
#        exit $exit_status
#    else
#        echo "[TEST INFO]: ---------frontend test passed---------"
#    fi
#}

function stop_docker() {
    cd $WORKPATH/docker/gaudi
    container_list=$(cat docker_compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    done
}

function main() {

    stop_docker
    # begin_time=$(date +%s)
    build_docker_images
    # start_time=$(date +%s)
    start_services
    # end_time=$(date +%s)
    # minimal_duration=$((end_time-start_time))
    # maximal_duration=$((end_time-begin_time))
    # echo "Mega service start duration is "$maximal_duration"s"

    # validate_microservices
    validate_megaservice
    # validate_frontend

    stop_docker
    echo y | docker system prune

}

main
