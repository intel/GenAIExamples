# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# import sys
# import os

# sys.path.append('/path/to/parent')  # Replace with the actual path to the parent folder

import os

# from VideoRAGQnA.utils import config_reader as reader
import sys

# Add the parent directory of the current script to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
VECTORDB_SERVICE_HOST_IP = os.getenv("VECTORDB_SERVICE_HOST_IP", "0.0.0.0")


import argparse
import json
import os

import chromadb

# sys.path.append(os.path.abspath('../utils'))
# import config_reader as reader
import yaml
from extract_store_frames import process_all_videos
from langchain_experimental.open_clip import OpenCLIPEmbeddings
from utils import config_reader as reader
from vector_stores import db

# EMBEDDING MODEL
clip_embd = OpenCLIPEmbeddings(model_name="ViT-g-14", checkpoint="laion2b_s34b_b88k")


def read_json(path):
    with open(path) as f:
        x = json.load(f)
    return x


def read_file(path):
    content = None
    with open(path, "r") as file:
        content = file.read()
    return content


def store_into_vectordb(metadata_file_path, selected_db):
    GMetadata = read_json(metadata_file_path)
    global_counter = 0

    total_videos = len(GMetadata.keys())

    for _, (video, data) in enumerate(GMetadata.items()):

        image_name_list = []
        embedding_list = []
        metadata_list = []
        ids = []

        # process frames
        frame_metadata = read_json(data["extracted_frame_metadata_file"])
        for frame_id, frame_details in frame_metadata.items():
            global_counter += 1
            if selected_db == "vdms":
                meta_data = {
                    "timestamp": frame_details["timestamp"],
                    "frame_path": frame_details["frame_path"],
                    "video": video,
                    "embedding_path": data["embedding_path"],
                    "date_time": frame_details["date_time"],  # {"_date":frame_details['date_time']},
                    "date": frame_details["date"],
                    "year": frame_details["year"],
                    "month": frame_details["month"],
                    "day": frame_details["day"],
                    "time": frame_details["time"],
                    "hours": frame_details["hours"],
                    "minutes": frame_details["minutes"],
                    "seconds": frame_details["seconds"],
                }
            if selected_db == "chroma":
                meta_data = {
                    "timestamp": frame_details["timestamp"],
                    "frame_path": frame_details["frame_path"],
                    "video": video,
                    "embedding_path": data["embedding_path"],
                    "date": frame_details["date"],
                    "year": frame_details["year"],
                    "month": frame_details["month"],
                    "day": frame_details["day"],
                    "time": frame_details["time"],
                    "hours": frame_details["hours"],
                    "minutes": frame_details["minutes"],
                    "seconds": frame_details["seconds"],
                }
            image_path = frame_details["frame_path"]
            image_name_list.append(image_path)

            metadata_list.append(meta_data)
            ids.append(str(global_counter))
            # print('datetime',meta_data['date_time'])
        # generate clip embeddings
        embedding_list.extend(clip_embd.embed_image(image_name_list))

        vs.add_images(uris=image_name_list, metadatas=metadata_list)

        print(
            f"✅ {_+1}/{total_videos} video {video}, len {len(image_name_list)}, {len(metadata_list)}, {len(embedding_list)}"
        )


def generate_image_embeddings(selected_db):
    if generate_frames:
        print("Processing all videos, Generated frames will be stored at")
        print(f"input video folder = {path}")
        print(f"frames output folder = {image_output_dir}")
        print(f"metadata files output folder = {meta_output_dir}")
        process_all_videos(path, image_output_dir, meta_output_dir, N, selected_db)

    global_metadata_file_path = meta_output_dir + "metadata.json"
    print(f"global metadata file available at {global_metadata_file_path}")
    store_into_vectordb(global_metadata_file_path, selected_db)


def retrieval_testing():
    Q = "man holding red basket"
    print(f"Testing Query {Q}")
    results = vs.MultiModalRetrieval(Q)

    ##print (results)


if __name__ == "__main__":
    # read config yaml
    print("Reading config file")
    # config = reader.read_config('../docs/config.yaml')

    # Create argument parser
    parser = argparse.ArgumentParser(description="Process configuration file for generating and storing embeddings.")

    # Add argument for configuration file
    parser.add_argument("config_file", type=str, help="Path to configuration file (e.g., config.yaml)")

    # Add argument for videos folder
    parser.add_argument("videos_folder", type=str, help="Path to folder containing videos")

    # Parse command-line arguments
    args = parser.parse_args()

    # Read configuration file
    config = reader.read_config(args.config_file)

    print("Config file data \n", yaml.dump(config, default_flow_style=False, sort_keys=False))

    generate_frames = config["generate_frames"]
    embed_frames = config["embed_frames"]
    path = config["videos"]  # args.videos_folder #
    image_output_dir = config["image_output_dir"]
    meta_output_dir = config["meta_output_dir"]
    N = config["number_of_frames_per_second"]

    host = VECTORDB_SERVICE_HOST_IP
    port = int(config["vector_db"]["port"])
    selected_db = config["vector_db"]["choice_of_db"]

    # Creating DB
    print(
        "Creating DB with text and image embedding support, \nIt may take few minutes to download and load all required models if you are running for first time."
    )
    print("Connect to {} at {}:{}".format(selected_db, host, port))

    vs = db.VS(host, port, selected_db)

    generate_image_embeddings(selected_db)

    retrieval_testing()
