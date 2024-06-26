# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import datetime
import json
import os
import random

import cv2
from tzlocal import get_localzone


def process_all_videos(path, image_output_dir, meta_output_dir, N, selected_db):

    def extract_frames(video_path, image_output_dir, meta_output_dir, N, date_time, local_timezone):
        video = video_path.split("/")[-1]
        # Create a directory to store frames and metadata
        os.makedirs(image_output_dir, exist_ok=True)
        os.makedirs(meta_output_dir, exist_ok=True)

        # Open the video file
        cap = cv2.VideoCapture(video_path)

        if int(cv2.__version__.split(".")[0]) < 3:
            fps = cap.get(cv2.cv.CV_CAP_PROP_FPS)
        else:
            fps = cap.get(cv2.CAP_PROP_FPS)

        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

        # print (f'fps {fps}')
        # print (f'total frames {total_frames}')

        mod = int(fps // N)
        if mod == 0:
            mod = 1

        print(f"total frames {total_frames}, N {N}, mod {mod}")

        # Variables to track frame count and desired frames
        frame_count = 0

        # Metadata dictionary to store timestamp and image paths
        metadata = {}

        while cap.isOpened():
            ret, frame = cap.read()

            if not ret:
                break

            frame_count += 1

            if frame_count % mod == 0:
                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # Convert milliseconds to seconds
                frame_path = os.path.join(image_output_dir, f"{video}_{frame_count}.jpg")
                time = date_time.strftime("%H:%M:%S")
                date = date_time.strftime("%Y-%m-%d")
                hours, minutes, seconds = map(float, time.split(":"))
                year, month, day = map(int, date.split("-"))

                cv2.imwrite(frame_path, frame)  # Save the frame as an image

                metadata[frame_count] = {
                    "timestamp": timestamp,
                    "frame_path": frame_path,
                    "date": date,
                    "year": year,
                    "month": month,
                    "day": day,
                    "time": time,
                    "hours": hours,
                    "minutes": minutes,
                    "seconds": seconds,
                }
                if selected_db == "vdms":
                    # Localize the current time to the local timezone of the machine
                    # Tahani might not need this
                    current_time_local = date_time.replace(tzinfo=datetime.timezone.utc).astimezone(local_timezone)

                    # Convert the localized time to ISO 8601 format with timezone offset
                    iso_date_time = current_time_local.isoformat()
                    metadata[frame_count]["date_time"] = {"_date": str(iso_date_time)}

        # Save metadata to a JSON file
        metadata_file = os.path.join(meta_output_dir, f"{video}_metadata.json")
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=4)

        # Release the video capture and close all windows
        cap.release()
        print(f"{frame_count/mod} Frames extracted and metadata saved successfully.")
        return fps, total_frames, metadata_file

    videos = [file for file in os.listdir(path) if file.endswith(".mp4")]

    # print (f'Total {len(videos)} videos will be processed')
    metadata = {}

    for i, each_video in enumerate(videos):
        video_path = os.path.join(path, each_video)
        date_time = datetime.datetime.now()
        print("date_time : ", date_time)
        # Get the local timezone of the machine
        local_timezone = get_localzone()
        fps, total_frames, metadata_file = extract_frames(
            video_path, image_output_dir, meta_output_dir, N, date_time, local_timezone
        )
        metadata[each_video] = {
            "fps": fps,
            "total_frames": total_frames,
            "extracted_frame_metadata_file": metadata_file,
            "embedding_path": f"embeddings/{each_video}.pt",
            "video_path": f"{path}/{each_video}",
        }
        print(f"✅  {i+1}/{len(videos)}")

    metadata_file = os.path.join(meta_output_dir, "metadata.json")
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=4)
