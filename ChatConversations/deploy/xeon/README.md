# Build Mega Service of Chat Conversations on Xeon

This document outlines the deployment process for a Chat Conversations application on Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution. Docker images will be published to Docker Hub soon, it will simplify the deployment process for this service.

## 🚀 Apply for Xeon Server on AWS

To apply for a Xeon server on AWS, start by creating an AWS account if you don't have one already. Then, head to the [EC2 Console](https://console.aws.amazon.com/ec2/v2/home) to begin the process. Within the EC2 service, select the Amazon EC2 M7i or M7i-flex instance type to leverage the power of 4th Generation Intel Xeon Scalable processors. These instances are optimized for high-performance computing and demanding workloads.

For detailed information about these instance types, you can refer to this [link](https://aws.amazon.com/ec2/instance-types/m7i/). Once you've chosen the appropriate instance type, proceed with configuring your instance settings, including network configurations, security groups, and storage options.

After launching your instance, you can connect to it using SSH (for Linux instances) or Remote Desktop Protocol (RDP) (for Windows instances). From there, you'll have full access to your Xeon server, allowing you to install, configure, and manage your applications as needed.

## 🚀 Setup for serving the LLMs

We will use vLLM running on CPU to serve the LLMs. For that, we will clone and build the docker image for vLLM. Please make sure you have git and docker installed with correct proxy configuration.

### 1. Clone the OPEA GenAI Components project

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 2. Build LLM Image

vLLM instance will be pre-configured to run on CPUs. Below are the steps to build the docker image for vLLM for serving LLMs on CPU.

```bash
cd comps/llms/text-generation/vllm && chmod +x build_docker_vllm.sh  && bash ./build_docker_vllm.sh
```

This build will take a while to complete. Once the build succeeds, run:

```bash
docker images | grep "vllm"
```

It will give you list of all vLLM images on your machine. If build is successful, the list should have a vLLM image with tag as `cpu`.

## 🚀 Setup and Run the ChatConversation Megaservice

Once we have built the vLLM image, we are ready to spin it up to start serving our models. We will utilize this vLLM image as part of our ChatConversation Megaservice. This ChatConversation MegaService constitutes several other microservices. Therefore, as soon as all other microservices are configured and setup, we will bring up our vLLM based model servers along with these microservices.

We will build and setup the MegaService using methods described below. First let's move back to our work directory, where we cloned the OPEA GenAI Components project. We are going to clone the repo containing our MegaService now:

### 1. Clone the Intel's OPEA Github repo.

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ChatConversations/deploy/xeon/
```

### 2. Setup Environment Variables

You need to setup some environment variables that will be used by the different microservices brought up the docker-compose file. They are injected into containers of these microservices via `docker-compose.yaml` file.

```bash
# Environment variables to set on your shell

host_ip=$(hostname -I | awk '{print $1}')
export MONGO_PORT=50001
export LLAMA2_PORT=50002
export NEURAL_CHAT_PORT=50003
export UI_PORT=50004
export CHAT_API_PORT=50005
export MONGO_HOST=${host_ip}
export OPEA_vLLM_LLAMA2_ENDPOINT="http://${host_ip}:${LLAMA2_PORT}/v1/"
export OPEA_vLLM_INTEL_NEURAL_CHAT_ENDPOINT="http://${host_ip}:${NEURAL_CHAT_PORT}/v1/"
export LLM_MODEL_ID_LLAMA="meta-llama/Llama-2-7b-chat-hf"
export LLM_MODEL_ID_NEURAL="Intel/neural-chat-7b-v3-3"
export CONVERSATION_URL="http://${host_ip}:${CHAT_API_PORT}"
export no_proxy=${no_proxy},"Your_External_Public_IP"
```

> _**Note**_: Please replace **Your_External_Public_IP** with your actual external public IP.

> _**Note**_: If `host_ip` does not contain your external IP, replace `host_ip` with you external IP address manually. Please do not use `localhost`.

Value provided as ports are just for example purpose and you can change them to any available port on your machine. You can run above export commands directly on your shell or add them to a file and run following command to set them all in a handy way:

```bash
source <file_name_with_path>
```

#### Setup HuggingFace Hub Token

You also need to acquire and setup HuggingFace Hub Token, in order to download your favorite models from Hugging Face. You can create an account on HuggingFace Hub and easily get an API token. Once you have it, run the following command to set your API token as an environment variable on your shell:

```bash
export HUGGING_FACE_HUB_TOKEN="Your_Huggingface_Hub_API_Token"
```

Replace `Your_Huggingface_Hub_API_Token` in above command with your actual token.

### 3. 🚀 Build and bring up the Megaservice

```bash
docker compose up -d --build
```

This will start the build process. Once the build succeeds, docker will spin up all the containers that are part of Megaservice (including the containers for vLLM images). There will be 2 containers for vLLM service as we are going to server 2 LLMs.

| :memo: Please make sure all the environment variables in previous step is setup properly, otherwise most of these containers will fail to start. |
| ------------------------------------------------------------------------------------------------------------------------------------------------ |

Verify that all the services are up and running using the following command:

```bash
docker ps -a
```

This should show the list of all running containers. In this list, you should find following five containers:

```bash
CONTAINER ID   IMAGE                                      COMMAND                  CREATED          STATUS          PORTS                                           NAMES
5df35ff1824f   opea/chat-conversation-ui-service:latest   "nginx -g 'daemon of…"   7 seconds ago   Up 3 seconds   0.0.0.0:50004->80/tcp, :::50004->80/tcp         xeon-ui-1
4d9d3a76dfff   mongo:7.0.11                               "docker-entrypoint.s…"   7 seconds ago   Up 3 seconds   0.0.0.0:50001->27017/tcp, :::50001->27017/tcp   xeon-mongodb-1
0ff48b03889c   vllm:cpu                                   "/bin/bash -c 'cd / …"   7 seconds ago   Up 3 seconds   0.0.0.0:50002->80/tcp, :::50002->80/tcp         xeon-vllm-llama2-1
7fc2d67b4174   vllm:cpu                                   "/bin/bash -c 'cd / …"   7 seconds ago   Up 3 seconds   0.0.0.0:50003->80/tcp, :::50003->80/tcp         xeon-vllm-neural-chat-1
cba7a1001b97   opea/chat-conversation-service:latest      "python3 main.py"        7 seconds ago   Up 3 seconds   0.0.0.0:50005->8002/tcp, :::50005->8002/tcp     xeon-chat-1
```

### Test the API Endpoints

The chatConversation service can dynamically communicate with different LLMs. Below are the commands to test the APIs targeting different LLMs.

```bash

curl -X 'POST' \
  'http://${host_ip}:8002/conversations?user=test' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": "What is Deep Learning",
  "temperature": 0.4,
  "model": "intel.neuralchat",
  "max_tokens": 500,
  "stream": false
}'

```

```bash

curl -X 'POST' \
  'http://${host_ip}:8002/conversations?user=test' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": "What is Deep Learning",
  "temperature": 0.4,
  "model": "meta.llama2.vllm",
  "max_tokens": 500,
  "stream": false
}'

```

## 🚀 Launch the UI

To access the frontend, open the following URL in your browser: http://{host_ip}:80. By default, the UI runs on port 80 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `docker-compose.yaml` file as shown below:

```yaml
ui:
  image: opea/ui-service
  container_name: ui-service
  build:
    context: ../../microservices/ui
  ports:
    - <new port>:80
```

![UI Screenshot](../../media/demo.png)

> ChatConversations Demo Screenshot
