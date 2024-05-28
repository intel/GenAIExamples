#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps

    docker build -t opea/embedding-tei:latest -f comps/embeddings/langchain/docker/Dockerfile .
    docker build -t opea/retriever-redis:latest -f comps/retrievers/langchain/docker/Dockerfile .
    docker build -t opea/reranking-tei:latest -f comps/reranks/langchain/docker/Dockerfile .
    docker build -t opea/llm-tgi:latest -f comps/llms/text-generation/tgi/Dockerfile .
    docker build -t opea/dataprep-redis:latest -f comps/dataprep/redis/docker/Dockerfile .

    cd $WORKPATH
    docker build --no-cache -t opea/chatqna:latest -f Dockerfile .

    cd $WORKPATH/ui
    docker build --no-cache -t opea/chatqna-ui:latest -f docker/Dockerfile .

    docker images
}

function start_services() {
    cd $WORKPATH/docker-composer/xeon

    export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
    export RERANK_MODEL_ID="BAAI/bge-reranker-large"
    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:6006"
    export TEI_RERANKING_ENDPOINT="http://${ip_address}:8808"
    export TGI_LLM_ENDPOINT="http://${ip_address}:9009"
    export REDIS_URL="redis://${ip_address}:6379"
    export INDEX_NAME="rag-redis"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export EMBEDDING_SERVICE_HOST_IP=${ip_address}
    export RETRIEVER_SERVICE_HOST_IP=${ip_address}
    export RERANK_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:8888/v1/chatqna"

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    # TODO: Replace the container name with a test-specific name

    docker compose -f docker_compose.yaml up -d
    n=0
    until [[ "$n" -ge 200 ]]; do
        docker logs tgi-service > tgi_service_start.log
        if grep -q Connected tgi_service_start.log; then
            break
        fi
        sleep 1s
        n=$((n+1))
    done
}

function validate_microservices() {
    # Check if the microservices are running correctly.
    # TODO: Any results check required??
    curl ${ip_address}:6006/embed \
        -X POST \
        -d '{"inputs":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/embed.log
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Microservice failed, please check the logs in artifacts!"
        docker logs tei-embedding-server >> ${LOG_PATH}/embed.log
        exit 1
    fi
    sleep 1s

    curl http://${ip_address}:6000/v1/embeddings \
        -X POST \
        -d '{"text":"hello"}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/embeddings.log
    if [ $exit_code -ne 0 ]; then
        echo "Microservice failed, please check the logs in artifacts!"
        docker logs embedding-tei-server >> ${LOG_PATH}/embeddings.log
        exit 1
    fi
    sleep 1m # retrieval can't curl as expected, try to wait for more time

    export PATH="${HOME}/miniforge3/bin:$PATH"
    source activate
    test_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    curl http://${ip_address}:7000/v1/retrieval \
        -X POST \
        -d '{"text":"What is the revenue of Nike in 2023?","embedding":${test_embedding}}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/retrieval.log
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Microservice failed, please check the logs in artifacts!"
        docker logs retriever-redis-server >> ${LOG_PATH}/retrieval.log
        exit 1
    fi
    sleep 1s

    curl http://${ip_address}:8808/rerank \
        -X POST \
        -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/rerank.log
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Microservice failed, please check the logs in artifacts!"
        docker logs tei-xeon-server >> ${LOG_PATH}/rerank.log
        exit 1
    fi
    sleep 1s

    curl http://${ip_address}:8000/v1/reranking -X POST \
        -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/reranking.log
    if [ $exit_code -ne 0 ]; then
        echo "Microservice failed, please check the logs in artifacts!"
        docker logs reranking-tei-xeon-server >> ${LOG_PATH}/reranking.log
        exit 1
    fi
    sleep 1s

    curl http://${ip_address}:9009/generate \
        -X POST \
        -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/generate.log
    if [ $exit_code -ne 0 ]; then
        echo "Microservice failed, please check the logs in artifacts!"
        docker logs tgi-service >> ${LOG_PATH}/generate.log
        exit 1
    fi
    sleep 1s

    curl http://${ip_address}:9000/v1/chat/completions \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/completions.log
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Microservice failed, please check the logs in artifacts!"
        docker logs llm-tgi-server >> ${LOG_PATH}/completions.log
        exit 1
    fi
    sleep 1s
}

function validate_megaservice() {
    # Curl the Mega Service
    http_proxy="" curl http://${ip_address}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
        "model": "Intel/neural-chat-7b-v3-3",
        "messages": "What is the revenue of Nike in 2023?"}' > ${LOG_PATH}/curl_megaservice.log
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Megaservice failed, please check the logs in artifacts!"
        docker logs chatqna-xeon-backend-server >> ${LOG_PATH}/curl_megaservice.log
        exit 1
    fi

    echo "Checking response results, make sure the output is reasonable. "
    local status=false
    if [[ -f $LOG_PATH/curl_megaservice.log ]] &&
        [[ $(grep -c "billion" $LOG_PATH/curl_megaservice.log) != 0 ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed, please check the logs in artifacts!"
        exit 1
    else
        echo "Response check succeed!"
    fi

    echo "Checking response format, make sure the output format is acceptable for UI."
    # TODO

}

function validate_frontend() {
    cd $WORKPATH/ui/svelte
    local conda_env_name="ChatQnA_e2e"
    export PATH=${HOME}/miniconda3/bin/:$PATH
    conda remove -n ${conda_env_name} --all -y
    conda create -n ${conda_env_name} python=3.12 -y
    source activate ${conda_env_name}

    sed -i "s/localhost/$ip_address/g" playwright.config.ts

    conda install -c conda-forge nodejs -y && npm install && npm ci && npx playwright install --with-deps
    node -v && npm -v && pip list

    npx playwright test || exit_status=$?

    if [ $exit_status -ne 0 ]; then
        echo "[TEST INFO]: ---------E2E test failed---------"
        exit $exit_status
    else
        echo "[TEST INFO]: ---------E2E test passed---------"
    fi

}

function stop_docker() {
    cd $WORKPATH/docker-composer/xeon
    container_list=$(cat docker_compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    done
}

function main() {

    stop_docker

    begin_time=$(date +%s)
    build_docker_images
    start_time=$(date +%s)
    start_services
    end_time=$(date +%s)
    minimal_duration=$((end_time-start_time))
    maximal_duration=$((end_time-begin_time))
    echo "Mega service start minimal duration is "$minimal_duration"s, maximal duration(including docker image build) is "$maximal_duration"s"

    validate_microservices
    validate_megaservice
    validate_frontend

    # stop_docker
    echo y | docker system prune

}

main
