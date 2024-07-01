# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Some code adapted from https://github.com/haotian-liu/LLaVA/blob/main/llava/serve/gradio_web_server.py
# and https://github.com/haotian-liu/LLaVA/blob/main/llava/conversation.py

import argparse
import base64
import os
from io import BytesIO

import gradio as gr
import requests

title_markdown = """
# 🌋 在 Gaudi2 上展示 LLaVA
"""

tos_markdown = """
### 使用条款
使用本服务即表示用户同意以下条款：
本服务为研究预览版，仅供非商业用途。它仅提供有限的安全措施，可能会生成冒犯性内容。严禁将本服务用于任何非法、有害、暴力、种族歧视或色情的目的。本服务可能会收集用户对话数据以用于未来研究。
为获得最佳体验，请使用台式电脑访问本演示，因为移动设备可能会影响其质量。
"""

block_css = """

#buttons button {
    min-width: min(120px,100%);
}

.upload-container .wrap,
.upload-container .wrap .or {
  color: #1f2937;
}


.upload-container .wrap .icon-wrap {
  color: #e5e7eb;
  margin-top: 4rem;
  width: 4rem;
  height: 3rem;
}


"""

no_change_btn = gr.Button()
enable_btn = gr.Button(interactive=True)
disable_btn = gr.Button(interactive=False)


def process_image(image, return_pil=False, image_format="PNG", max_len=1344, min_len=672):
    if max(image.size) > max_len:
        max_hw, min_hw = max(image.size), min(image.size)
        aspect_ratio = max_hw / min_hw
        shortest_edge = int(min(max_len / aspect_ratio, min_len, min_hw))
        longest_edge = int(shortest_edge * aspect_ratio)
        W, H = image.size
        if H > W:
            H, W = longest_edge, shortest_edge
        else:
            H, W = shortest_edge, longest_edge
        image = image.resize((W, H))
    if return_pil:
        return image
    else:
        buffered = BytesIO()
        image.save(buffered, format=image_format)
        img_b64_str = base64.b64encode(buffered.getvalue()).decode()
        return img_b64_str


def handle_llava_request(text, image, max_new_tokens, chat_history):
    print(f"text: {text}, image: {image}, max_new_tokens: {max_new_tokens}\n")
    img_b64_str = process_image(image, return_pil=False, image_format="JPEG")
    img_str = f'<img src="data:image/jpeg;base64,{img_b64_str}" alt="user upload image" />'

    # skip embedding the image in latter messages
    if len(chat_history) < 1:
        msg = img_str + text.replace("<image>", "").strip()
    else:
        msg = text.replace("<image>", "").strip()

    req_dict = {"prompt": f"<image>\nUSER: {text}\nASSISTANT:", "image": img_b64_str, "max_new_tokens": max_new_tokens}
    result = requests.post(f"{args.worker_addr}/generate", json=req_dict, proxies={"http": None})
    answer = result.json()["text"]

    chat_history.append([msg, answer])
    return [chat_history] + [enable_btn]


def clear_history(chat_history, image, text):
    chat_history = []
    image = None
    text = None
    return [chat_history, image, text] + [disable_btn]


def build_demo(embed_mode, cur_dir=None, concurrency_count=10):
    textbox = gr.Textbox(show_label=False, placeholder="输入文字并按回车键", container=False)
    with gr.Blocks(title="LLaVA", theme=gr.themes.Default(), css=block_css) as demo:
        # demo.add(custom_html)

        state = gr.State()

        if not embed_mode:
            gr.Markdown(title_markdown)

        with gr.Row():
            with gr.Column(scale=3):
                imagebox = gr.Image(type="pil", label="图片", interactive=True, elem_id="my_imagebox")

                if cur_dir is None:
                    cur_dir = os.path.dirname(os.path.abspath(__file__))
                gr.Examples(
                    examples=[
                        [f"{cur_dir}/resources/extreme_ironing.jpg", "这张图片有什么不寻常之处？"],
                        [
                            f"{cur_dir}/resources/waterview.jpg",
                            "当我去那里访问时，我应该注意哪些事情？",
                        ],
                    ],
                    label="请选择一个示例",
                    inputs=[imagebox, textbox],
                )

                with gr.Accordion("参数", open=False) as parameter_row:
                    max_output_tokens = gr.Slider(
                        minimum=0,
                        maximum=1024,
                        value=512,
                        step=64,
                        interactive=True,
                        label="最大输出标记数",
                    )

            with gr.Column(scale=8):
                chatbot = gr.Chatbot(
                    elem_id="chatbot",
                    label="LLaVA聊天机器人",
                    height=650,
                    layout="panel",
                )
                with gr.Row():
                    with gr.Column(scale=8):
                        textbox.render()
                    with gr.Column(scale=1, min_width=50):
                        submit_btn = gr.Button(value="发送", variant="primary")
                with gr.Row(elem_id="buttons") as button_row:
                    clear_btn = gr.Button(value="🗑️  清除", interactive=False)

        if not embed_mode:
            gr.Markdown(tos_markdown)

        btn_list = [clear_btn]

        clear_btn.click(
            clear_history,
            [chatbot, imagebox, textbox],
            [chatbot, imagebox, textbox] + btn_list,
        )

        textbox.submit(
            handle_llava_request,
            [textbox, imagebox, max_output_tokens, chatbot],
            [chatbot] + btn_list,
        )

        submit_btn.click(
            handle_llava_request,
            [textbox, imagebox, max_output_tokens, chatbot],
            [chatbot] + btn_list,
        )

    return demo


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # frontend host and port
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int)
    # backend worker address
    parser.add_argument(
        "--worker-addr", type=str, default="http://localhost:8085", help="The worker address of the LLaVA server."
    )
    parser.add_argument("--share", action="store_true")
    parser.add_argument("--embed", action="store_true")
    parser.add_argument("--concurrency-count", type=int, default=16)

    args = parser.parse_args()
    print(args)
    demo = build_demo(args.embed, concurrency_count=args.concurrency_count)

    demo.queue(api_open=False).launch(server_name=args.host, server_port=args.port, share=args.share)
