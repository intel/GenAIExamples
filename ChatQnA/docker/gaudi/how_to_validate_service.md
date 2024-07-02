# How to Check and Validate Micro Service in the GenAI Example

GenAI examples build mega-services on top of the micro-service and server.
To make mega-service works, each micro service and server must work as expected.

Take the ChatQnA as an example, this document shows how to start a GenAI example.

Assumption: build all docker images already

Here are steps to check the micro service and server.

## 1. Check environment variables

Make sure environment variables are set

start the docker containers

```
cd ./GenAIExamples/ChatQnA/docker/gaudi
docker compose -f ./docker_compose.yaml up -d
```

Check the start up log by `docker compose -f ./docker/gaudi/docker_compose.yaml logs`.
Where the docker_compose.yaml file is the mega service docker-compose configuration.
The warning messages point out the veriabls are **NOT** set.

```
ubuntu@gaudi-vm:~/GenAIExamples/ChatQnA/docker/gaudi$ docker compose -f ./docker_compose.yaml up -d
WARN[0000] The "LANGCHAIN_API_KEY" variable is not set. Defaulting to a blank string.
WARN[0000] The "LANGCHAIN_TRACING_V2" variable is not set. Defaulting to a blank string.
WARN[0000] The "LANGCHAIN_API_KEY" variable is not set. Defaulting to a blank string.
WARN[0000] The "LANGCHAIN_TRACING_V2" variable is not set. Defaulting to a blank string.
WARN[0000] The "LANGCHAIN_API_KEY" variable is not set. Defaulting to a blank string.
WARN[0000] The "LANGCHAIN_TRACING_V2" variable is not set. Defaulting to a blank string.
WARN[0000] The "LANGCHAIN_API_KEY" variable is not set. Defaulting to a blank string.
WARN[0000] The "LANGCHAIN_TRACING_V2" variable is not set. Defaulting to a blank string.
WARN[0000] /home/ubuntu/GenAIExamples/ChatQnA/docker/gaudi/docker_compose.yaml: `version` is obsolete
```

## 2. Check the docker container status

Check the docker containers are started

For example, the ChatQnA example starts 11 docker (services), check these docker containers are all running, i.e, all the contaniers `STATUS` are `Up`

run the command `docker ps -a`

Here is the output:

```
CONTAINER ID   IMAGE                                                   COMMAND                  CREATED         STATUS                          PORTS                                                                                  NAMES
28d9a5570246   opea/chatqna-ui:latest                                  "docker-entrypoint.s…"   2 minutes ago   Up 2 minutes                    0.0.0.0:5173->5173/tcp, :::5173->5173/tcp                                              chatqna-gaudi-ui-server
bee1132464cd   opea/chatqna:latest                                     "python chatqna.py"      2 minutes ago   Up 2 minutes                    0.0.0.0:8888->8888/tcp, :::8888->8888/tcp                                              chatqna-gaudi-backend-server
f810f3b4d329   opea/embedding-tei:latest                               "python embedding_te…"   2 minutes ago   Up 2 minutes                    0.0.0.0:6000->6000/tcp, :::6000->6000/tcp                                              embedding-tei-server
325236a01f9b   opea/llm-tgi:latest                                     "python llm.py"          2 minutes ago   Up 2 minutes                    0.0.0.0:9000->9000/tcp, :::9000->9000/tcp                                              llm-tgi-gaudi-server
2fa17d84605f   opea/dataprep-redis:latest                              "python prepare_doc_…"   2 minutes ago   Up 2 minutes                    0.0.0.0:6007->6007/tcp, :::6007->6007/tcp                                              dataprep-redis-server
69e1fb59e92c   opea/retriever-redis:latest                             "/home/user/comps/re…"   2 minutes ago   Up 2 minutes                    0.0.0.0:7000->7000/tcp, :::7000->7000/tcp                                              retriever-redis-server
313b9d14928a   opea/reranking-tei:latest                               "python reranking_te…"   2 minutes ago   Up 2 minutes                    0.0.0.0:8000->8000/tcp, :::8000->8000/tcp                                              reranking-tei-gaudi-server
05c40b636239   ghcr.io/huggingface/tgi-gaudi:1.2.1                     "text-generation-lau…"   2 minutes ago   Exited (1) About a minute ago                                                                                          tgi-gaudi-server
174bd43fa6b5   opea/tei-gaudi:latest                                   "text-embeddings-rou…"   2 minutes ago   Up 2 minutes                    0.0.0.0:8090->80/tcp, :::8090->80/tcp                                                  tei-embedding-gaudi-server
74084469aa33   redis/redis-stack:7.2.0-v9                              "/entrypoint.sh"         2 minutes ago   Up 2 minutes                    0.0.0.0:6379->6379/tcp, :::6379->6379/tcp, 0.0.0.0:8001->8001/tcp, :::8001->8001/tcp   redis-vector-db
88399dbc9e43   ghcr.io/huggingface/text-embeddings-inference:cpu-1.2   "text-embeddings-rou…"   2 minutes ago   Up 2 minutes                    0.0.0.0:8808->80/tcp, :::8808->80/tcp                                                  tei-reranking-gaudi-server
```

In this case, `ghcr.io/huggingface/tgi-gaudi:1.2.1` Existed.

```
05c40b636239   ghcr.io/huggingface/tgi-gaudi:1.2.1                     "text-generation-lau…"   2 minutes ago   Exited (1) About a minute ago                                                                                          tgi-gaudi-server
```

Next we can check the container logs to get to know what happened during the docker start.

## 3. Check docker container log

Check the log of container by:

`docker logs <CONTAINER ID> -t`

View the logs of `ghcr.io/huggingface/tgi-gaudi:1.2.1`

#docker logs 05c40b636239 -t

```
...
2024-06-05T01:56:48.959581881Z   File "/usr/local/lib/python3.10/dist-packages/torch/nn/modules/module.py", line 833, in _apply
2024-06-05T01:56:48.959583925Z     param_applied = fn(param)
2024-06-05T01:56:48.959585811Z
2024-06-05T01:56:48.959587629Z   File "/usr/local/lib/python3.10/dist-packages/torch/nn/modules/module.py", line 1161, in convert
2024-06-05T01:56:48.959589733Z     return t.to(device, dtype if t.is_floating_point() or t.is_complex() else None, non_blocking)
2024-06-05T01:56:48.959591795Z
2024-06-05T01:56:48.959593607Z   File "/usr/local/lib/python3.10/dist-packages/habana_frameworks/torch/core/weight_sharing.py", line 53, in __torch_function__
2024-06-05T01:56:48.959595769Z     return super().__torch_function__(func, types, new_args, kwargs)
2024-06-05T01:56:48.959597800Z
2024-06-05T01:56:48.959599622Z RuntimeError: synStatus=9 [Device-type mismatch] Device acquire failed.
2024-06-05T01:56:48.959601665Z  rank=0
2024-06-05T01:56:49.053352819Z 2024-06-05T01:56:49.053251Z ERROR text_generation_launcher: Shard 0 failed to start
2024-06-05T01:56:49.053373989Z 2024-06-05T01:56:49.053279Z  INFO text_generation_launcher: Shutting down shards
2024-06-05T01:56:49.053385371Z Error: ShardCannotStart
```

The log shows `RuntimeError: synStatus=9 [Device-type mismatch] Device acquire failed.` This means the service fail to acquire the device.

So just make sure the devices are available.

Here is another failure example:

```
f7a08f9867f9   ghcr.io/huggingface/tgi-gaudi:1.2.1                     "text-generation-lau…"   16 seconds ago   Exited (2) 14 seconds ago                                                                                          tgi-gaudi-server
```

Check the log by `docker logs f7a08f9867f9 -t`.

```
2024-06-05T01:30:30.695934928Z error: a value is required for '--model-id <MODEL_ID>' but none was supplied
2024-06-05T01:30:30.697123534Z
2024-06-05T01:30:30.697148330Z For more information, try '--help'.
```

The log indicates the MODLE_ID is not set.

View the docker input parameters in `./ChatQnA/docker/gaudi/docker_compose.yaml`

```
  tgi-service:
    image: ghcr.io/huggingface/tgi-gaudi:1.2.1
    container_name: tgi-gaudi-server
    ports:
      - "8008:80"
    volumes:
      - "./data:/data"
    environment:
      http_proxy: ${http_proxy}
      https_proxy: ${https_proxy}
      HF_TOKEN: ${HUGGINGFACEHUB_API_TOKEN}
      HABANA_VISIBLE_DEVICES: all
      OMPI_MCA_btl_vader_single_copy_mechanism: none
    runtime: habana
    cap_add:
      - SYS_NICE
    ipc: host
    command: --model-id ${LLM_MODEL_ID}
```

The input MODEL_ID is `${LLM_MODEL_ID}`

Check environment variable `LLM_MODEL_ID` is set correctly, spelled correctly.
Set the LLM_MODEL_ID then restart the containers.

Also you can check overall logs with the following command, where the docker_compose.yaml is the mega service docker-compose configuration file.

```
docker compose -f ./docker-composer/gaudi/docker_compose.yaml logs
```

## 4. Check each micro service used by the Mega Service

### 1 TEI Embedding Service

```
curl ${host_ip}:8090/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

This test the embedding service. It sends "What is Deep Learning?" to the embedding service, the output is the embedding result of the sentences, it is a list of vector.
`[[0.00030903306,-0.06356524,0.0025720573,-0.012404448,0.050649878, ... , -0.02776986,-0.0246678,0.03999176,0.037477136,-0.006806653,0.02261455,-0.04570737,-0.033122733,0.022785513,0.0160026,-0.021343587,-0.029969815,-0.0049176104]]`

**Note**: The vector dimension are decided by the embedding model and the output value is dependent on model and input data.

### 2 Embedding Microservice

```
curl http://${host_ip}:6000/v1/embeddings\
  -X POST \
  -d '{"text":"What is Deep Learning?"}' \
  -H 'Content-Type: application/json'
```

This test the embedding microservice. In this test, it sends out `What is Deep Learning?` to embedding.
Embedding microservice get input data, call embedding service to embedding data.
Embedding server are with NO state, but microservice keep the state. There is `id` in the output of `Embedding Microservice`.

```
{"id":"e8c85e588a235a4bc4747a23b3a71d8f","text":"What is Deep Learning?","embedding":[0.00030903306,-0.06356524,0.0025720573,-0.012404448,0.050649878, ...,   0.02776986,-0.0246678,0.03999176,0.037477136,-0.006806653,0.02261455,-0.04570737,-0.033122733,0.022785513,0.0160026,-0.021343587,-0.029969815,-0.0049176104]}
```

### 3 Retriever Microservice

To consume the retriever microservice, you need to generate a mock embedding vector by Python script.
The length of embedding vector is determined by the embedding model.
Here we use the model `EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"`, [the model dimension is 768](https://huggingface.co/BAAI/bge-base-en-v1.5).

Check the vecotor dimension of your embedding model, set `your_embedding` dimension equals to it.

```
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://${host_ip}:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"test\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```

The output is retrieved text that relevant to the input data:

```
{"id":"27210945c7c6c054fa7355bdd4cde818","retrieved_docs":[{"id":"0c1dd04b31ab87a5468d65f98e33a9f6","text":"Company: Nike. financial instruments are subject to master netting arrangements that allow for the offset of assets and liabilities in the event of default or early termination of the contract.\nAny amounts of cash collateral received related to these instruments associated with the Company's credit-related contingent features are recorded in Cash and\nequivalents and Accrued liabilities, the latter of which would further offset against the Company's derivative asset balance. Any amounts of cash collateral posted related\nto these instruments associated with the Company's credit-related contingent features are recorded in Prepaid expenses and other current assets, which would further\noffset against the Company's derivative liability balance. Cash collateral received or posted related to the Company's credit-related contingent features is presented in the\nCash provided by operations component of the Consolidated Statements of Cash Flows. The Company does not recognize amounts of non-cash collateral received, such\nas securities, on the Consolidated Balance Sheets. For further information related to credit risk, refer to Note 12 — Risk Management and Derivatives.\n2023 FORM 10-K 68Table of Contents\nThe following tables present information about the Company's derivative assets and liabilities measured at fair value on a recurring basis and indicate the level in the fair\nvalue hierarchy in which the Company classifies the fair value measurement:\nMAY 31, 2023\nDERIVATIVE ASSETS\nDERIVATIVE LIABILITIES"},{"id":"1d742199fb1a86aa8c3f7bcd580d94af","text": ... }

```

### 4 TEI Reranking Service

Reranking service

```
curl http://${host_ip}:8808/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```

Output is:
`[{"index":1,"score":0.9988041},{"index":0,"score":0.022948774}]`

It socres the input

### 5 Reranking Microservice

```
curl http://${host_ip}:8000/v1/reranking\
  -X POST \
  -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
  -H 'Content-Type: application/json'
```

Here is the output:

```
{"id":"e1eb0e44f56059fc01aa0334b1dac313","query":"Human: Answer the question based only on the following context:\n    Deep learning is...\n    Question: What is Deep Learning?","max_new_tokens":1024,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}
```

You may notice reranking microservice are with state ('ID' and other meta data), while reranking service are not.

### 6 TGI Service

```
curl http://${host_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":64, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

TGI service generate text for the input prompt. Here is the expected result from TGI output:

```
{"generated_text":"We have all heard the buzzword, but our understanding of it is still growing. It’s a sub-field of Machine Learning, and it’s the cornerstone of today’s Machine Learning breakthroughs.\n\nDeep Learning makes machines act more like humans through their ability to generalize from very large"}
```

**NOTE**: After launch the TGI, it takes minutes for TGI server to load LLM model and warm up.

If you get

```
curl: (7) Failed to connect to 100.81.104.168 port 8008 after 0 ms: Connection refused
```

and the log shows model warm up, please wait for a while and try it later.

```
2024-06-05T05:45:27.707509646Z 2024-06-05T05:45:27.707361Z  WARN text_generation_router: router/src/main.rs:357: `--revision` is not set
2024-06-05T05:45:27.707539740Z 2024-06-05T05:45:27.707379Z  WARN text_generation_router: router/src/main.rs:358: We strongly advise to set it to a known supported commit.
2024-06-05T05:45:27.852525522Z 2024-06-05T05:45:27.852437Z  INFO text_generation_router: router/src/main.rs:379: Serving revision bdd31cf498d13782cc7497cba5896996ce429f91 of model Intel/neural-chat-7b-v3-3
2024-06-05T05:45:27.867833811Z 2024-06-05T05:45:27.867759Z  INFO text_generation_router: router/src/main.rs:221: Warming up model
```

### 7 LLM Microservice

```
curl http://${host_ip}:9000/v1/chat/completions\
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
  -H 'Content-Type: application/json'
```

You will get generated text from LLM:

```
data: b'\n'

data: b'\n'

data: b'Deep'

data: b' learning'

data: b' is'

data: b' a'

data: b' subset'

data: b' of'

data: b' machine'

data: b' learning'

data: b' that'

data: b' uses'

data: b' algorithms'

data: b' to'

data: b' learn'

data: b' from'

data: b' data'

data: [DONE]
```

### 8 MegaService

```
curl http://${host_ip}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
     "model": "Intel/neural-chat-7b-v3-3",
     "messages": "What is the revenue of Nike in 2023?"
     }'
```

Here it the output for your reference:

```
data: b'\n'

data: b'An'

data: b'swer'

data: b':'

data: b' In'

data: b' fiscal'

data: b' '

data: b'2'

data: b'0'

data: b'2'

data: b'3'

data: b','

data: b' N'

data: b'I'

data: b'KE'

data: b','

data: b' Inc'

data: b'.'

data: b' achieved'

data: b' record'

data: b' Rev'

data: b'en'

data: b'ues'

data: b' of'

data: b' $'

data: b'5'

data: b'1'

data: b'.'

data: b'2'

data: b' billion'

data: b'.'

data: b'</s>'

data: [DONE]

```

**[Finished]** Congratulation! All your services work as expected now!
