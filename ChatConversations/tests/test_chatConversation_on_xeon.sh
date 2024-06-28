#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
PROJECT_NAME="${PROJECT_NAME:-test-chat}"
service_name_chat="chat"
service_name_llama="vllm-llama2"
service_name_neuralchat="vllm-neural-chat"

function build_docker_images() {
    cd $WORKPATH/deploy/xeon
    export CHAT_API_PORT=${CHAT_API_PORT:-50005}
    export MONGO_PORT=${MONGO_PORT:-50001}
    export LLAMA2_PORT=${LLAMA2_PORT:-50002}
    export NEURAL_CHAT_PORT=${NEURAL_CHAT_PORT:-50003}
    export UI_PORT=${UI_PORT:-50004}
    export MONGO_HOST=${ip_address}
    export CHAT_API_PORT=${CHAT_API_PORT:-50005}
    export HF_TOKEN=${HUGGING_FACE_HUB_TOKEN}
    export OPEA_vLLM_LLAMA2_ENDPOINT="http://${ip_address}:${LLAMA2_PORT}/v1"
    export OPEA_vLLM_INTEL_NEURAL_CHAT_ENDPOINT="http://${ip_address}:${NEURAL_CHAT_PORT}/v1"
    export CONVERSATION_URL="http://${ip_address}:${CHAT_API_PORT}"
    export LLM_MODEL_ID_LLAMA="meta-llama/Llama-2-7b-chat-hf"
    export LLM_MODEL_ID_NEURAL="Intel/neural-chat-7b-v3-3"
    docker compose build --no-cache
}

function start_services() {
    cd $WORKPATH/deploy/xeon

    # Start Docker Containers
    # TODO: Replace the container name with a test-specific name

    docker compose -f docker-compose.yaml -p ${PROJECT_NAME} up -d
    n=0
    until [[ "$n" -ge 400 ]]; do
        docker logs "${PROJECT_NAME}-${service_name_llama}-1" &> ${service_name_llama}.log
        echo "Waiting for vLLM service - ${n}sec"
        if grep -q "Avg prompt throughput" ${service_name_llama}.log; then
            break
        fi
        sleep 1s
        n=$((n+1))
    done
    docker ps | grep ${PROJECT_NAME}
}

function validate_services() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    echo "Sending request and waiting for LLM response. This may take a while."
    local HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."

        echo "Sending request again and waiting for LLM response. This may take a while."
        local CONTENT=$(curl -s -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/${SERVICE_NAME}.log)

        if echo "$CONTENT" | grep -qi "$EXPECTED_RESULT"; then
            echo "[ $SERVICE_NAME ] Content is as expected."
        else
            echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
            docker logs ${DOCKER_NAME} &>> ${LOG_PATH}/${SERVICE_NAME}.log
            exit 1
        fi
    else
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs ${DOCKER_NAME} &>> ${LOG_PATH}/${SERVICE_NAME}.log
        exit 1
    fi
    sleep 1s
}

function validate_microservices() {
    # Check if the microservices are running correctly.

    # LLAMA2 LLM microservice
    echo "Validating microservice [ ${service_name_llama} ]:"
    validate_services \
        "${OPEA_vLLM_LLAMA2_ENDPOINT}/chat/completions" \
        "Deep learning " \
        "${service_name_llama}" \
        "${PROJECT_NAME}-${service_name_llama}-1" \
        '{"model": "'${LLM_MODEL_ID_LLAMA}'","messages": [{"role": "user", "content": "What is Deep Learning"}]}'

    # Neural chat LLM microservice
    echo "Validating microservice [ ${service_name_neuralchat} ]:"
    validate_services \
        "${OPEA_vLLM_INTEL_NEURAL_CHAT_ENDPOINT}/chat/completions" \
        "Deep learning " \
        "${service_name_neuralchat}" \
        "${PROJECT_NAME}-${service_name_neuralchat}-1" \
        '{"model": "'${LLM_MODEL_ID_NEURAL}'","messages": [{"role": "user", "content": "What is Deep Learning"}]}'
}

function validate_megaservice() {
    # Curl the Mega Service

    echo "Validating megaservice [ ${service_name_chat} ]:"
    validate_services \
        "${CONVERSATION_URL}/conversations?user=test" \
        "Deep Learning" \
        "${service_name_chat}" \
        "${PROJECT_NAME}-${service_name_chat}-1" \
        '{"messages": "What is Deep Learning","temperature": 0.1,"model": "meta.llama2.vllm","max_tokens": 500,"stream": false}'
}


function stop_docker() {
    container_list=$(docker ps --format "table {{.Names}}" | grep -e "${PROJECT_NAME}*")
    for container_name in $container_list; do
        echo "Stopping ${container_name}"
        cid=$(docker ps -aq --filter "name=$container_name")
        if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s && echo "Done"; fi
    done
}

function main() {

    stop_docker
    set -e

    begin_time=$(date +%s)
    build_docker_images
    start_time=$(date +%s)
    start_services
    end_time=$(date +%s)
    echo ${end_time}
    minimal_duration=$((end_time-start_time))
    maximal_duration=$((end_time-begin_time))
    echo ${minimal_duration}
    echo "Mega service start minimal duration is ${minimal_duration}s, maximal duration(including docker image build) is ${maximal_duration}s" && sleep 1s

    validate_microservices
    validate_megaservice

    stop_docker
    echo y | docker system prune

}

main
