#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Array of YAML file names
yaml_files=("qna_configmap_gaudi" "redis-vector-db"  "tgi_gaudi_service" "tei_embedding_gaudi_service" "tei_reranking_service" "retriever" "reranking" "embedding"  "llm" "chaqna-xeon-backend-server" "chaqna-gaudi-ui-server" "dataprep-redis-service", "tgi_gaudi_service_without_rag")
for element in ${yaml_files[@]}
do
    echo "Applying manifest from ${element}.yaml"
    kubectl apply -f "${element}.yaml"
done
