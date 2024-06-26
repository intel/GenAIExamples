# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import datetime
from typing import Iterable, List, Optional

import chromadb
from dateparser.search import search_dates
from langchain_community.vectorstores import VDMS, Chroma
from langchain_community.vectorstores.vdms import VDMS_Client
from langchain_core.runnables import ConfigurableField
from langchain_experimental.open_clip import OpenCLIPEmbeddings
from tzlocal import get_localzone


class VS:

    def __init__(self, host, port, selected_db):
        self.host = host
        self.port = port
        self.selected_db = selected_db

        # initializing important variables
        self.client = None
        self.image_db = None
        self.image_embedder = OpenCLIPEmbeddings(model_name="ViT-g-14", checkpoint="laion2b_s34b_b88k")
        self.image_collection = "image-test"
        self.text_retriever = None
        self.image_retriever = None

        # initialize_db
        self.get_db_client()
        self.init_db()

    def get_db_client(self):

        if self.selected_db == "chroma":
            print("Connecting to Chroma db server . . .")
            self.client = chromadb.HttpClient(host=self.host, port=self.port)

        if self.selected_db == "vdms":
            print("Connecting to VDMS db server . . .")
            self.client = VDMS_Client(host=self.host, port=self.port)

    def init_db(self):
        print("Loading db instances")
        if self.selected_db == "chroma":
            self.image_db = Chroma(
                client=self.client,
                embedding_function=self.image_embedder,
                collection_name=self.image_collection,
            )

        if self.selected_db == "vdms":
            self.image_db = VDMS(
                client=self.client,
                embedding=self.image_embedder,
                collection_name=self.image_collection,
                engine="FaissFlat",
            )

        self.image_retriever = self.image_db.as_retriever(search_type="mmr").configurable_fields(
            search_kwargs=ConfigurableField(
                id="k_image_docs",
                name="Search Kwargs",
                description="The search kwargs to use",
            )
        )

    def update_db(self, prompt, n_images):
        print("Update DB")

        base_date = datetime.datetime.today()
        today_date = base_date.date()
        dates_found = search_dates(prompt, settings={"PREFER_DATES_FROM": "past", "RELATIVE_BASE": base_date})
        # if no date is detected dates_found should return None
        if dates_found != None:
            # Print the identified dates
            # print("dates_found:",dates_found)
            for date_tuple in dates_found:
                date_string, parsed_date = date_tuple
                print(f"Found date: {date_string} -> Parsed as: {parsed_date}")
                date_out = str(parsed_date.date())
                time_out = str(parsed_date.time())
                hours, minutes, seconds = map(float, time_out.split(":"))
                year, month, day_out = map(int, date_out.split("-"))

            # print("today's date", base_date)
            rounded_seconds = min(round(parsed_date.second + 0.5), 59)
            parsed_date = parsed_date.replace(second=rounded_seconds, microsecond=0)

            # Convert the localized time to ISO format
            iso_date_time = parsed_date.isoformat()
            iso_date_time = str(iso_date_time)

            if self.selected_db == "vdms":
                if date_string == "today":
                    constraints = {"date": ["==", date_out]}
                    self.update_image_retriever = self.image_db.as_retriever(
                        search_type="mmr", search_kwargs={"k": n_images, "filter": constraints}
                    )
                elif date_out != str(today_date) and time_out == "00:00:00":  ## exact day (example last friday)
                    constraints = {"date": ["==", date_out]}
                    self.update_image_retriever = self.image_db.as_retriever(
                        search_type="mmr", search_kwargs={"k": n_images, "filter": constraints}
                    )

                elif (
                    date_out == str(today_date) and time_out == "00:00:00"
                ):  ## when search_date interprates words as dates output is todays date + time 00:00:00
                    self.update_image_retriever = self.image_db.as_retriever(
                        search_type="mmr", search_kwargs={"k": n_images}
                    )
                else:  ## Interval  of time:last 48 hours, last 2 days,..
                    constraints = {"date_time": [">=", {"_date": iso_date_time}]}
                    self.update_image_retriever = self.image_db.as_retriever(
                        search_type="mmr", search_kwargs={"k": n_images, "filter": constraints}
                    )
            if self.selected_db == "chroma":
                if date_string == "today":
                    self.update_image_retriever = self.image_db.as_retriever(
                        search_type="mmr", search_kwargs={"k": n_images, "filter": {"date": {"$eq": date_out}}}
                    )
                elif date_out != str(today_date) and time_out == "00:00:00":  ## exact day (example last friday)
                    self.update_image_retriever = self.image_db.as_retriever(
                        search_type="mmr", search_kwargs={"k": n_images, "filter": {"date": {"$eq": date_out}}}
                    )
                elif (
                    date_out == str(today_date) and time_out == "00:00:00"
                ):  ## when search_date interprates words as dates output is todays date + time 00:00:00
                    self.update_image_retriever = self.image_db.as_retriever(
                        search_type="mmr", search_kwargs={"k": n_images}
                    )
                else:  ## Interval  of time:last 48 hours, last 2 days,..
                    constraints = {"date_time": [">=", {"_date": iso_date_time}]}
                    self.update_image_retriever = self.image_db.as_retriever(
                        search_type="mmr",
                        search_kwargs={
                            "filter": {
                                "$or": [
                                    {
                                        "$and": [
                                            {"date": {"$eq": date_out}},
                                            {
                                                "$or": [
                                                    {"hours": {"$gte": hours}},
                                                    {
                                                        "$and": [
                                                            {"hours": {"$eq": hours}},
                                                            {"minutes": {"$gte": minutes}},
                                                        ]
                                                    },
                                                ]
                                            },
                                        ]
                                    },
                                    {
                                        "$or": [
                                            {"month": {"$gt": month}},
                                            {"$and": [{"day": {"$gt": day_out}}, {"month": {"$eq": month}}]},
                                        ]
                                    },
                                ]
                            },
                            "k": n_images,
                        },
                    )
        else:
            self.update_image_retriever = self.image_db.as_retriever(search_type="mmr", search_kwargs={"k": n_images})

    def length(self):
        if self.selected_db == "chroma":
            images = self.image_db.__len__()
            return (texts, images)

        if self.selected_db == "vdms":
            pass

        return (None, None)

    def delete_collection(self, collection_name):
        self.client.delete_collection(collection_name=collection_name)

    def add_images(
        self,
        uris: List[str],
        metadatas: Optional[List[dict]] = None,
    ):

        self.image_db.add_images(uris, metadatas)

    def MultiModalRetrieval(
        self,
        query: str,
        n_images: Optional[int] = 3,
    ):

        self.update_db(query, n_images)
        image_results = self.update_image_retriever.invoke(query)

        for r in image_results:
            print("images:", r.metadata["video"], "\t", r.metadata["date"], "\t", r.metadata["time"], "\n")

        return image_results
