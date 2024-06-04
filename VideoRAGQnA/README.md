# Video RAG

## Introduction

Video RAG is a framework that retrieves video based on provided user prompt. It uses both video scene description generated by open source vision models (ex video-llama, video-llava etc.) as text embeddings and frames as image embeddings to perform vector similarity search. The provided solution also supports feature to retrieve more similar videos without prompting it. (see the example video below)

![Example Video](docs/visual-rag-demo.gif)

## Tools

- **UI**: streamlit
- **Vector Storage**: Chroma DB **or** Intel's VDMS
- **Image Embeddings**: CLIP
- **Text Embeddings**: all-MiniLM-L12-v2
- **RAG Retriever**: Langchain Ensemble Retrieval

## Prerequisites

There are 10 example videos present in `video_ingest/videos` along with their description generated by open-source vision model.
If you want these video RAG to work on your own videos, make sure it matches below format.

## File Structure

```bash
video_ingest/
.
├── scene_description
│   ├── op_10_0320241830.mp4.txt
│   ├── op_1_0320241830.mp4.txt
│   ├── op_19_0320241830.mp4.txt
│   ├── op_21_0320241830.mp4.txt
│   ├── op_24_0320241830.mp4.txt
│   ├── op_31_0320241830.mp4.txt
│   ├── op_47_0320241830.mp4.txt
│   ├── op_5_0320241915.mp4.txt
│   ├── op_DSCF2862_Rendered_001.mp4.txt
│   └── op_DSCF2864_Rendered_006.mp4.txt
└── videos
    ├── op_10_0320241830.mp4
    ├── op_1_0320241830.mp4
    ├── op_19_0320241830.mp4
    ├── op_21_0320241830.mp4
    ├── op_24_0320241830.mp4
    ├── op_31_0320241830.mp4
    ├── op_47_0320241830.mp4
    ├── op_5_0320241915.mp4
    ├── op_DSCF2862_Rendered_001.mp4
    └── op_DSCF2864_Rendered_006.mp4
```

## Setup and Installation

Install pip requirements

```bash
cd VideoRAGQnA
pip3 install -r docs/requirements.txt
```

The current framework supports both Chroma DB and Intel's VDMS, use either of them,

Running Chroma DB as docker container

```bash
docker run -d -p 8000:8000 chromadb/chroma
```

**or**

Running VDMS DB as docker container

```bash
docker run -d -p 55555:55555 intellabs/vdms:latest
```

**Note:** If you are not using file structure similar to what is described above, consider changing it in `config.yaml`.

Update your choice of db and port in `config.yaml`.

```bash
export VECTORDB_SERVICE_HOST_IP=<ip of host where vector db is running>

export HUGGINGFACEHUB_API_TOKEN='<your HF token>'
```

HuggingFace hub API token can be generated [here](https://huggingface.co/login?next=%2Fsettings%2Ftokens).

Generating Image embeddings and store them into selected db, specify config file location and video input location

```bash
python3 embedding/generate_store_embeddings.py docs/config.yaml video_ingest/videos/
```

**Web UI Video RAG**

```bash
streamlit run video-rag-ui.py --server.address 0.0.0.0 --server.port 50055
```