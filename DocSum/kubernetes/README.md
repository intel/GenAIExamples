<h1 align="center" id="title">Deploy DocSum in Kubernetes Cluster</h1>

This document outlines the deployment process for a Document Summary (DocSum) application that utilizes the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice components on Intel Xeon servers and Gaudi machines.
The DocSum Service leverages a Kubernetes operator called genai-microservices-connector(GMC). GMC supports connecting microservices to create pipelines based on the specification in the pipeline yaml file, in addition it allows the user to dynamically control which model is used in a service such as an LLM or embedder. The underlying pipeline language also supports using external services that may be running in public or private clouds elsewhere.

Please install GMC in your Kubernetes cluster, if you have not already done so, by following the steps in Section "Getting Started" at [GMC Install](https://github.com/opea-project/GenAIInfra/tree/main/microservices-connector#readme). We will soon publish images to Docker Hub, at which point no builds will be required, further simplifying install.

The DocSum application is defined as a Custom Resource (CR) file that the above GMC operator acts upon. It first checks if the microservices listed in the CR yaml file are running, if not it starts them and then proceeds to connect them. When the DocSum RAG pipeline is ready, the service endpoint details are returned, letting you use the application. Should you use "kubectl get pods" commands you will see all the component microservices, in particular embedding, retriever, rerank, and llm.

The DocSum pipeline uses  prebuilt images. The Xeon version uses the prebuilt image llm-docsum-tgi:latest which internally leverages the
the image ghcr.io/huggingface/text-generation-inference:1.4. The service is called tgi-svc. Meanwhile, the Gaudi version launches the
service tgi-gaudi-svc, which uses the image ghcr.io/huggingface/tgi-gaudi:1.2.1. Both TGI model services serve the model specified in the LLM_MODEL_ID variable that is exported by you. In the below example we use Intel/neural-chat-7b-v3-3.

[NOTE]
Please refer to [Docker Xeon README](https://github.com/opea-project/GenAIExamples/blob/main/DocSum/docker/xeon/README.md) or
[Docker Gaudi README](https://github.com/opea-project/GenAIExamples/blob/main/DocSum/docker/gaudi/README.md) to build the OPEA images. 
These will be available on Docker Hub soon, simplifying installation.

## Deploy the RAG pipeline
This involves deploying the application pipeline custom resource. You can use docsum_xeon.yaml if you have just a Xeon cluster or docsum_gaudi.yaml if you have a Gaudi cluster.

1. Setup Environment variables. These are specific to the user. Skip the proxy settings if you are not operating behind one.

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export ns=${docsum}
```

2. Create namespace for the application and deploy it
```bash
kubectl create ns ${ns}
kubectl apply -f $(pwd)/docsum_xeon.yaml
```

3. GMC will reconcile the custom resource and get all related components/services ready. Confirm the service status using below command
```bash
kubectl get service -n ${ns}
```

4. Obtain the custom resource/pipeline access URL

```bash
kubectl get gmconnectors.gmc.opea.io -n ${ns}
NAME     URL                                                      READY     AGE
docsum   http://router-service.docsum.svc.cluster.local:8080      8/0/8     3m
```

5. Deploy a client pod to test the application

```bash
kubectl create deployment client-test -n ${ns} --image=python:3.8.13 -- sleep infinity
```

6. Access the pipeline using the above URL from the client pod and execute a request

```bash
export CLIENT_POD=$(kubectl get pod -l app=client-test -o jsonpath={.items..metadata.name})
export accessUrl=$(kubectl get gmc -n $ns -o jsonpath="{.items[?(@.metadata.name=='docsum')].status.accessUrl}")
kubectl exec "$CLIENT_POD" -n $ns -- curl $accessUrl -X POST -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'  -H 'Content-Type: application/json'
```

7. Clean up. Use standard Kubernetes custom resource remove commands. Confirm cleaned by retrieving pods in application namespace.
