# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import threading
import time
from typing import Any, List, Mapping, Optional

import gradio as gr
import torch
from embedding.vector_stores import db
from langchain.llms.base import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, set_seed
from utils import config_reader as reader
from utils import prompt_handler as ph

# from vector_stores import db
# HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
HUGGINGFACEHUB_API_TOKEN = "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"

set_seed(22)
import argparse

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

VECTORDB_SERVICE_HOST_IP = os.getenv("VECTORDB_SERVICE_HOST_IP", "0.0.0.0")


CSS = """

.custom_login-btn {
    width: 100% !important;
    display: block !important;
    color: white !important;
    background: rgb(0 118 189) !important;
    background-fill-secondary: var(--neutral-50);
    --border-color-accent: var(--primary-300);
    --border-color-primary: var(--neutral-200);

}
.context_container{

    border: 1px solid black;
    padding: 0px;

}

.passwordContainer{
    width: 30% !important;
    padding: 20px;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, 50%);

}

.video-class {
  width: 100%; /* Set the width of the container */
  height: 100%; /* Set the height of the container */
  position: relative; /* Position the video relative to the container */
  overflow: hidden; /* Hide overflow content */
}

.video-class video {
  width: 100%; /* Set video width to fill container */
  height: 100%; /* Set video height to fill container */
  object-fit: cover; /* Stretch and fill the video to cover the entire container */
}


.custom_submit-btn_2 {
    display: block !important;
    background: #fed7aa !important;
    color: #ea580c !important;
    background-fill-secondary: var(--neutral-50);
    --border-color-accent: var(--primary-300);
    --border-color-primary: var(--neutral-200);

}


.custom_submit-btn{
    background: rgb(240,240,240) !important;
    color: rgb(118 118 118) !important;
    font-size: 13px;
}
.custom_submit-btn:hover{
    background: rgb(0 118 189) !important;
    color: white !important;
    font-size: 16px;
}

.custom_blue-btn {
    display: block !important;
    background: rgb(0 118 189) !important;
    color: white !important;
    background-fill-secondary: var(--neutral-50);
    --border-color-accent: var(--primary-300);
    --border-color-primary: var(--neutral-200);

}

.return-btn {
    display: block !important;
    background: rgb(0 0 0) !important;
    color: white !important;
    background-fill-secondary: var(--neutral-50);
    --border-color-accent: var(--primary-300);
    --border-color-primary: var(--neutral-200);
}
video {

  object-fit: cover; /* Stretch and fill the video to cover the entire container */


}

"""


def load_models():
    # print("HF Token: ", HUGGINGFACEHUB_API_TOKEN)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype=torch.float32, device_map=device, trust_remote_code=True, token=HUGGINGFACEHUB_API_TOKEN
    )

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True, token=HUGGINGFACEHUB_API_TOKEN)
    tokenizer.padding_size = "right"
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True)

    return model, tokenizer, streamer


class CustomLLM(LLM):

    @torch.inference_mode()
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        streamer: Optional[TextIteratorStreamer] = None,  # Add streamer as an argument
    ) -> str:

        tokens = tokenizer.encode(prompt, return_tensors="pt")
        input_ids = tokens.to(device)
        with torch.no_grad():
            output = model.generate(
                input_ids=input_ids,
                max_new_tokens=500,
                num_return_sequences=1,
                num_beams=1,
                min_length=1,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.2,
                length_penalty=1,
                temperature=0.1,
                streamer=streamer,
                # pad_token_id=tokenizer.eos_token_id,
                do_sample=True,
            )

    def stream_res(self, prompt):
        thread = threading.Thread(target=self._call, args=(prompt, None, None, streamer))  # Pass streamer to _call
        thread.start()

        for text in streamer:
            yield text

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return model_path  # {"name_of_model": model_path}

    @property
    def _llm_type(self) -> str:
        return "custom"


def videoSearch(query):
    results = vs.MultiModalRetrieval(query)
    result = [i.metadata["video"] for i in results]
    # result += [i.metadata['frame_path'] for i in results]
    result.sort()
    result = list(set(result))
    result = [["video_ingest/videos/" + i, i] for i in result]
    return result, [[None, "Hello"]]


def bot(chatbot, input_message, Gallery, selection):
    print(selection, "====")
    try:
        context = "video_ingest/scene_description/" + Gallery[selection][1] + ".txt"
        with open(context) as f:
            context = f.read()
    except:
        context = "No video is selected, tell the client to select a video."
    formatted_prompt = ph.get_formatted_prompt(context, input_message, chatbot[-1])
    response = chatbot + [[input_message, ""]]
    for new_text in llm.stream_res(formatted_prompt):
        response[-1][1] += new_text

        yield response, ""


def select_fn(data: gr.SelectData):
    print(data.index)
    print(data.value)
    return data.index, [[None, "Hello"]]


scheme = (
    "#FFFFFF",
    "#FAFAFA",
    "#F5F5F5",
    "#F0F0F0",
    "#E8E8E8",
    "#E0E0E0",
    "#D6D6D6",
    "#C2C2C2",
    "#A8A8A8",
    "#8D8D8D",
    "#767676",
)


def spawnUI(share_gradio, server_port, server_name):
    with gr.Blocks(
        css=CSS, theme=gr.themes.Base(primary_hue=gr.themes.Color(*scheme), secondary_hue=gr.themes.colors.blue)
    ) as demo:

        # chatUI =
        with gr.Group():
            gr.Label("# Visual Rag", show_label=False)
            examples = gr.Dropdown(
                [  #'Enter Text',
                    # 'Find similar videos',
                    "Man wearing glasses",
                    "People reading item description",
                    "Man holding red shopping basket",
                    "Was there any person wearing a blue shirt seen today?",
                    "Was there any person wearing a blue shirt seen in the last 6 hours?",
                    "Was there any person wearing a blue shirt seen last Sunday?",
                    "Was a person wearing glasses seen in the last 30 minutes?",
                    "Was a person wearing glasses seen in the last 72 hours?",
                ],
                label="Video search",
                allow_custom_value=True,
            )
            with gr.Row(visible=True, elem_classes=["chatbot-widget"]) as chatUI:
                with gr.Column(scale=10):
                    chatbot = gr.Chatbot(
                        layout="panel",
                        bubble_full_width=True,
                        avatar_images=["images.jpeg", "images.png"],
                        show_label=False,
                        container=False,
                        height=600,
                        value=[
                            [
                                None,
                                "Hello, welcome to Visual Rag! To get started, select a question from the drop-down menu above. \n Then, click on your selection and type your question below to chat with the video",
                            ]
                        ],
                    )
                    # with gr.Group():
                    with gr.Row():
                        message = gr.Textbox(placeholder="Type a message...", show_label=False, scale=9)
                        submit = gr.Button("Submit", elem_classes=["custom_blue-btn"], scale=1)
                        # with gr.Row() as return_div:

                        #     back = gr.Button("↩️ Return", elem_classes=["custom_submit-btn"])
                        #     retry = gr.Button("🔄 Retry", elem_classes=["custom_submit-btn"])
                        #     clear = gr.Button("🗑️ Clear", elem_classes=["custom_submit-btn"])
                with gr.Column(scale=5):
                    # Video = gr.Video(show_label = False, container = False)
                    Gallery = gr.Gallery(label="Retrieved Videos", interactive=False)
                    selection = gr.Number(0, visible=False)
        Gallery.select(select_fn, None, [selection, chatbot], queue=False)
        examples.change(fn=videoSearch, inputs=examples, outputs=[Gallery, chatbot])
        # loginbutton.click(validate, [username, password], [LogInPage, chatUI, error_message], queue=False)
        message.submit(bot, [chatbot, message, Gallery, selection], [chatbot, message])
        submit.click(bot, [chatbot, message, Gallery, selection], [chatbot, message])
    demo.queue().launch(share=share_gradio, server_port=server_port, server_name=server_name)


if __name__ == "__main__":
    print("Reading config file")
    # config = reader.read_config('../docs/config.yaml')

    # Create argument parser
    parser = argparse.ArgumentParser(description="Process configuration file for generating and storing embeddings.")

    # Add argument for configuration file
    parser.add_argument("config_file", type=str, help="Path to configuration file (e.g., config.yaml)")

    parser.add_argument(
        "share_gradio",
        type=bool,
        help="whether to create a publicly shareable link for the gradio app. Creates an SSH tunnel to make your UI accessible from anywhere",
    )

    parser.add_argument(
        "server_name",
        type=str,
        default=None,
        help='to make app accessible on local network, set this to "0.0.0.0". Can be set by environment variable GRADIO_SERVER_NAME.',
    )

    parser.add_argument(
        "server_port",
        type=int,
        default=None,
        help="will start gradio app on this port (if available). Can be set by environment variable GRADIO_SERVER_PORT. ",
    )

    # Parse command-line arguments
    args = parser.parse_args()

    # Read configuration file
    config = reader.read_config(args.config_file)
    share_gradio = args.share_gradio
    server_port = args.server_port
    server_name = args.server_name

    model_path = config["model_path"]
    video_dir = config["videos"]
    print(video_dir)
    video_dir = video_dir.replace("../", "")

    model, tokenizer, streamer = load_models()
    llm = CustomLLM()

    host = VECTORDB_SERVICE_HOST_IP
    port = int(config["vector_db"]["port"])
    selected_db = config["vector_db"]["choice_of_db"]

    vs = db.VS(host, port, selected_db)
    spawnUI(share_gradio, server_port, server_name)
