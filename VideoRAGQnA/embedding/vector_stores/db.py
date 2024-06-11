import chromadb
from langchain_community.vectorstores import VDMS
from langchain_community.vectorstores.vdms import VDMS_Client
from langchain_experimental.open_clip import OpenCLIPEmbeddings
from langchain.pydantic_v1 import BaseModel, root_validator
from langchain_core.embeddings import Embeddings
from decord import VideoReader, cpu
import numpy as np
from langchain_community.vectorstores import Chroma
from typing import List, Optional, Iterable, Dict, Any
from langchain_core.runnables import ConfigurableField
from dateparser.search import search_dates
import datetime
from tzlocal import get_localzone
from embedding.adaclip_modeling.simple_tokenizer import SimpleTokenizer
from embedding.adaclip_datasets.preprocess import get_transforms
from einops import rearrange
from PIL import Image
import torch
import uuid

# 'similarity', 'similarity_score_threshold' (needs threshold), 'mmr'
chosen_video_search_type = "similarity"

#'mobilenet_v3_large', 'mobilenet'
backbone = 'mobilenet_v3_large'

class AdaCLIPEmbeddings(BaseModel, Embeddings):
    """AdaCLIP Embeddings model."""

    model: Any
    preprocess: Any
    tokenizer: Any
    # Select model: https://github.com/mlfoundations/open_clip
    model_name: str = "ViT-H-14"
    checkpoint: str = "laion2b_s32b_b79k"

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that open_clip and torch libraries are installed."""
        try:
            # Use the provided model if present
            if "model" not in values:
                raise ValueError("Model must be provided during initialization.")
            values["preprocess"] = get_transforms
            values["tokenizer"] = SimpleTokenizer()

        except ImportError:
            raise ImportError(
                "Please ensure AdaCLIP model is loaded"
            )
        return values

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        model_device = next(self.model.clip.parameters()).device
        text_features = []
        for text in texts:
            # Tokenize the text
            if isinstance(text, str):
                text = [text]

            sot_token = self.tokenizer.encoder["<|startoftext|>"]
            eot_token = self.tokenizer.encoder["<|endoftext|>"]
            tokens = [[sot_token] + self.tokenizer.encode(text) + [eot_token] for text in texts]
            tokenized_text = torch.zeros((len(tokens), 64), dtype=torch.int64)
            for i in range(len(tokens)):
                if len(tokens[i]) > 64:
                    tokens[i] = tokens[i][:64-1] + tokens[i][-1:]
                tokenized_text[i, :len(tokens[i])] = torch.tensor(tokens[i])
            text_embd, word_embd = self.model.get_text_output(tokenized_text.unsqueeze(0).to(model_device), return_hidden=False)

            # Normalize the embeddings
            print(" --->>>> text_embd.shape:", text_embd.shape)
            text_embd = rearrange(text_embd, "b n d -> (b n) d")
            text_embd = text_embd / text_embd.norm(dim=-1, keepdim=True)

            # Convert normalized tensor to list and add to the text_features list
            embeddings_list = text_embd.squeeze(0).tolist()
            text_features.append(embeddings_list)

        return text_features


    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


    def embed_video(self, paths: List[str]) -> List[List[float]]:
        # Open images directly as PIL images

        video_features = []
        for vid_path in paths:
            # Encode the video to get the embeddings
            model_device = next(self.model.parameters()).device
            # Preprocess the video for the model
            videos_tensor, policy_images_tensor = self.load_video_for_adaclip(vid_path, num_frm=64,
                                                                              no_policy=False,
                                                                              policy_backbone=backbone,
                                                                              max_img_size=224)
            embeddings_tensor = self.model.get_video_embeddings(videos_tensor.unsqueeze(0).to(model_device), policy_images_tensor.unsqueeze(0).to(model_device))

            # Convert tensor to list and add to the video_features list
            embeddings_list = embeddings_tensor.squeeze(0).tolist()

            video_features.append(embeddings_list)

        return video_features


    def load_video_for_adaclip(self, vis_path, num_frm=64, no_policy=False, policy_backbone='mobilenet_v3_large', max_img_size=224):
        # Load video with VideoReader
        vr = VideoReader(vis_path, ctx=cpu(0))
        num_frames = len(vr)

        frame_idx = np.linspace(0, num_frames, num=num_frm, endpoint=False, dtype=int) # Uniform sampling

        clip_images = []
        policy_images = []

        # Extract frames as numpy array
        img_array = vr.get_batch(frame_idx).asnumpy() # img_array = [T,H,W,C]
        clip_imgs = [Image.fromarray(img_array[j]) for j in range(img_array.shape[0])]

        # preprocess images
        for i in range(len(clip_imgs)):
            im = clip_imgs[i]
            clip_images.append(get_transforms("clip", max_img_size)(im)) # 3, 224, 224
            if not no_policy:
                policy_images.append(get_transforms(policy_backbone, 256)(im))

        clip_images_tensor = torch.zeros((num_frm,) + clip_images[0].shape)
        clip_images_tensor[:num_frm] = torch.stack(clip_images)
        if policy_images is not None:
            policy_images_tensor = torch.zeros((num_frm,) + policy_images[0].shape)
            policy_images_tensor[:num_frm] = torch.stack(policy_images)

        if policy_images:
            return clip_images_tensor, policy_images_tensor
        else:
            return clip_images_tensor, None


class VS:

    def __init__(self, host, port, selected_db):
        self.host = host
        self.port = port
        self.selected_db = selected_db

        # initializing important variables
        self.client = None
        self.image_db = None
        self.image_embedder = OpenCLIPEmbeddings(model_name="ViT-g-14", checkpoint="laion2b_s34b_b88k")
        self.image_collection = 'image-test'
        self.text_retriever = None
        self.image_retriever = None

        # initialize_db
        self.get_db_client()
        self.init_db()

    def get_db_client(self):

        if self.selected_db == 'chroma':
            print ('Connecting to Chroma db server . . .')
            self.client = chromadb.HttpClient(host=self.host, port=self.port)

        if self.selected_db == 'vdms':
            print ('Connecting to VDMS db server . . .')
            self.client = VDMS_Client(host=self.host, port=self.port)

    def init_db(self):
        print ('Loading db instances')
        if self.selected_db ==  'chroma':
            self.image_db = Chroma(
                client = self.client,
                embedding_function = self.image_embedder,
                collection_name = self.image_collection,
            )

        if self.selected_db == 'vdms':
            self.image_db = VDMS (
                client = self.client,
                embedding = self.image_embedder,
                collection_name = self.image_collection,
                engine = "FaissFlat",
            )

        self.image_retriever = self.image_db.as_retriever(search_type="mmr").configurable_fields(
            search_kwargs=ConfigurableField(
                id="k_image_docs",
                name="Search Kwargs",
                description="The search kwargs to use",
            )
        )


    def update_db(self, prompt, n_images):
        print ('Update DB')

        base_date = datetime.datetime.today()
        today_date= base_date.date()
        dates_found =search_dates(prompt, settings={'PREFER_DATES_FROM': 'past', 'RELATIVE_BASE': base_date})
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
            rounded_seconds = min(round(parsed_date.second + 0.5),59)
            parsed_date = parsed_date.replace(second=rounded_seconds, microsecond=0)

            # Convert the localized time to ISO format
            iso_date_time = parsed_date.isoformat()
            iso_date_time = str(iso_date_time)

            if self.selected_db == 'vdms':
                if date_string == 'today':
                    constraints = {"date": [ "==", date_out]}
                    self.update_image_retriever = self.image_db.as_retriever(search_type="mmr", search_kwargs={'k':n_images, "filter":constraints})
                elif date_out != str(today_date) and time_out =='00:00:00': ## exact day (example last firday)
                    constraints = {"date": [ "==", date_out]}
                    self.update_image_retriever = self.image_db.as_retriever(search_type="mmr", search_kwargs={'k':n_images, "filter":constraints})

                elif date_out == str(today_date) and time_out =='00:00:00': ## when search_date interprates words as dates output is todays date + time 00:00:00
                    self.update_image_retriever = self.image_db.as_retriever(search_type="mmr", search_kwargs={'k':n_images})
                else: ## Interval  of time:last 48 hours, last 2 days,..
                    constraints = {"date_time": [ ">=", {"_date":iso_date_time}]}
                    self.update_image_retriever = self.image_db.as_retriever(search_type="mmr", search_kwargs={'k':n_images, "filter":constraints})
            if self.selected_db == 'chroma':
                if date_string == 'today':
                    self.update_image_retriever = self.image_db.as_retriever(search_type="mmr", search_kwargs={'k':n_images, 'filter': {'date': {'$eq': date_out}}})
                elif date_out != str(today_date) and time_out =='00:00:00': ## exact day (example last firday)
                    self.update_image_retriever = self.image_db.as_retriever(search_type="mmr", search_kwargs={'k':n_images, 'filter': {'date': {'$eq': date_out}}})
                elif date_out == str(today_date) and time_out =='00:00:00': ## when search_date interprates words as dates output is todays date + time 00:00:00
                    self.update_image_retriever = self.image_db.as_retriever(search_type="mmr", search_kwargs={'k':n_images})
                else: ## Interval  of time:last 48 hours, last 2 days,..
                    constraints = {"date_time": [ ">=", {"_date":iso_date_time}]}
                    self.update_image_retriever = self.image_db.as_retriever(search_type="mmr", search_kwargs={'filter': {
                            "$or": [
                                {
                                    "$and": [
                                        {
                                            'date': {
                                                '$eq': date_out
                                            }
                                        },
                                        {
                                            "$or": [
                                                {
                                                    'hours': {
                                                        '$gte': hours
                                                    }
                                                },
                                                {
                                                    "$and": [
                                                        {
                                                            'hours': {
                                                                '$eq': hours
                                                                }
                                                        },
                                                        {
                                                            'minutes': {
                                                                '$gte': minutes
                                                                }
                                                        }
                                                    ]
                                                }
                                            ]

                                        }
                                    ]
                                },
                                {
                                    "$or": [
                                        {
                                            'month': {
                                                '$gt': month
                                            }
                                        },
                                        {
                                            "$and": [
                                                {
                                                    'day': {
                                                        '$gt': day_out
                                                    }
                                                },
                                                {
                                                    'month': {
                                                        '$eq': month
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        'k':n_images})
        else:
            self.update_image_retriever = self.image_db.as_retriever(search_type=chosen_video_search_type, search_kwargs={'k':n_images})

    def length(self):
        if self.selected_db == 'chroma':
            images = self.image_db.__len__()
            return (texts, images)

        if self.selected_db == 'vdms':
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
            print("images:", r.metadata['video'], '\t',r.metadata['date'], '\t',r.metadata['time'], '\n')

        return image_results


class VideoVS(VS):
    def __init__(self, host, port, selected_db, video_retriever_model):
        super().__init__(host, port, selected_db)
        self.video_collection = 'video-test'
        self.video_embedder = AdaCLIPEmbeddings(model=video_retriever_model)

        if self.selected_db == 'chroma':
            self.video_db = Chroma(
                client=self.client,
                embedding_function=self.video_embedder,
                collection_name=self.video_collection,
            )
        elif self.selected_db == 'vdms':
            self.video_db = VDMS(
                client=self.client,
                embedding=self.video_embedder,
                collection_name=self.video_collection,
                engine="FaissFlat",
            )

        self.video_retriever = self.video_db.as_retriever(search_type=chosen_video_search_type).configurable_fields(
            search_kwargs=ConfigurableField(
                id="k_video_docs",
                name="Search Kwargs",
                description="The search kwargs to use",
            )
        )

    
    def MultiModalRetrieval(self, query: str, n_videos: Optional[int] = 3):
        self.update_db(query, n_videos)
        video_results = self.video_retriever.invoke(query)

        for r in video_results:
            print("videos:", r.metadata['video_path'], '\t', r.metadata['date'], '\t', r.metadata['time'], '\n')

        return video_results