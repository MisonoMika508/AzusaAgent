# -*- coding: utf-8 -*-

"""
ComfyUI Agent Tool

作用：
1. 使用固定的 ComfyUI 工作流
2. Agent 只负责提供 positive_prompt / negative_prompt
3. 自动提交到 ComfyUI
4. 等待生成完成
5. 下载生成图片到 Agent/generated_images/
6. 返回图片路径给 Agent

ComfyUI 默认地址：
http://127.0.0.1:8188
"""

import os
import json
import time
import uuid
import urllib.request
import urllib.parse
import urllib.error


# ============================================================
# 基础路径
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

GENERATED_IMAGE_DIR = os.path.join(
    BASE_DIR,
    "generated_images"
)

os.makedirs(
    GENERATED_IMAGE_DIR,
    exist_ok=True
)


# ============================================================
# ComfyUI 地址
# ============================================================

COMFYUI_URL = (
    os.environ.get(
        "COMFYUI_URL",
        "http://127.0.0.1:8188"
    )
    .rstrip("/")
)


# ============================================================
# ComfyUI Tool 定义
#
# 这个对象会被 ollama_client.py 加入 TOOLS。
# ============================================================

COMFYUI_TOOL = {
    "type": "function",
    "function": {
        "name": "generate_comfyui_image",
        "description": (
            "使用已经配置好的 ComfyUI 工作流生成图片。"
            "Agent 只需要提供正面提示词和负面提示词。"
            "不要通过鼠标操作 ComfyUI。"
            "不要修改模型、LoRA、分辨率、采样器、步数等工作流参数。"
            "工具会自动提交工作流、等待生成完成并返回生成图片路径。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "positive_prompt": {
                    "type": "string",
                    "description": (
                        "图片正面提示词。"
                        "描述希望生成的角色、场景、动作、"
                        "画面构图、光照、画风等。"
                    ),
                },
                "negative_prompt": {
                    "type": "string",
                    "description": (
                        "图片负面提示词。"
                        "描述需要避免的画面问题。"
                    ),
                },
            },
            "required": [
                "positive_prompt",
                "negative_prompt",
            ],
        },
    },
}


# ============================================================
# HTTP JSON
# ============================================================

def _http_post_json(
    url,
    data,
    timeout=30
):
    """
    POST JSON 到 ComfyUI。
    """

    body = json.dumps(
        data,
        ensure_ascii=False
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout
    ) as response:

        response_data = (
            response.read()
            .decode("utf-8")
        )

    if not response_data:
        return {}

    return json.loads(
        response_data
    )


# ============================================================
# HTTP GET JSON
# ============================================================

def _http_get_json(
    url,
    timeout=30
):
    """
    GET JSON。
    """

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
        },
        method="GET",
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout
    ) as response:

        response_data = (
            response.read()
            .decode("utf-8")
        )

    if not response_data:
        return {}

    return json.loads(
        response_data
    )


# ============================================================
# 下载图片
# ============================================================

def _download_image(
    filename,
    subfolder,
    image_type,
    save_path
):
    """
    从 ComfyUI /view 下载图片。
    """

    query = urllib.parse.urlencode({

        "filename":
            filename,

        "subfolder":
            subfolder or "",

        "type":
            image_type or "output",

    })

    url = (
        COMFYUI_URL
        + "/view?"
        + query
    )

    request = urllib.request.Request(
        url,
        method="GET",
    )

    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:

        image_data = response.read()

    with open(
        save_path,
        "wb"
    ) as f:

        f.write(
            image_data
        )

    return save_path


# ============================================================
# 构建固定工作流
# ============================================================

def _build_workflow(
    positive_prompt,
    negative_prompt
):
    """
    根据用户提供的 ComfyUI 工作流，
    构建 API 格式工作流。

    Agent 只能修改：
        节点 2：正面提示词
        节点 3：负面提示词

    其他参数全部固定。
    """

    workflow = {

        # ----------------------------------------------------
        # Checkpoint
        # ----------------------------------------------------

        "1": {
            "class_type":
                "CheckpointLoaderSimple",

            "inputs": {
                "ckpt_name":
                    "Illustrious-XL-v1.1.safetensors",
            },
        },

        # ----------------------------------------------------
        # LoRA
        # ----------------------------------------------------

        "11": {
            "class_type":
                "LoraLoader",

            "inputs": {

                "model": [
                    "1",
                    0
                ],

                "clip": [
                    "1",
                    1
                ],

                "lora_name":
                    "BArtstyle-KREA2-V2-1024.safetensors",

                "strength_model":
                    0.8,

                "strength_clip":
                    0.8,
            },
        },

        # ----------------------------------------------------
        # 正面提示词
        # ----------------------------------------------------

        "2": {
            "class_type":
                "CLIPTextEncode",

            "inputs": {

                "text":
                    positive_prompt,

                "clip": [
                    "11",
                    1
                ],
            },
        },

        # ----------------------------------------------------
        # 负面提示词
        # ----------------------------------------------------

        "3": {
            "class_type":
                "CLIPTextEncode",

            "inputs": {

                "text":
                    negative_prompt,

                "clip": [
                    "11",
                    1
                ],
            },
        },

        # ----------------------------------------------------
        # KSampler
        # ----------------------------------------------------

        "4": {
            "class_type":
                "KSampler",

            "inputs": {

                "seed":
                    123456789,

                "control_after_generate":
                    "fixed",

                "steps":
                    28,

                "cfg":
                    6,

                "sampler_name":
                    "dpmpp_2m",

                "scheduler":
                    "karras",

                "denoise":
                    1.0,

                "model": [
                    "11",
                    0
                ],

                "positive": [
                    "2",
                    0
                ],

                "negative": [
                    "3",
                    0
                ],

                "latent_image": [
                    "7",
                    0
                ],
            },
        },

        # ----------------------------------------------------
        # 空 Latent
        # ----------------------------------------------------

        "7": {
            "class_type":
                "EmptyLatentImage",

            "inputs": {

                "width":
                    1152,

                "height":
                    1024,

                "batch_size":
                    1,
            },
        },

        # ----------------------------------------------------
        # VAE
        # ----------------------------------------------------

        "8": {
            "class_type":
                "VAEDecode",

            "inputs": {

                "samples": [
                    "4",
                    0
                ],

                "vae": [
                    "1",
                    2
                ],
            },
        },

        # ----------------------------------------------------
        # PreviewImage
        # ----------------------------------------------------

        "9": {
            "class_type":
                "PreviewImage",

            "inputs": {

                "images": [
                    "8",
                    0
                ],
            },
        },
    }

    return workflow


# ============================================================
# 查找生成结果
# ============================================================

def _find_generated_images(
    history_data
):
    """
    从 ComfyUI history 中提取生成图片。
    """

    images = []

    if not isinstance(
        history_data,
        dict
    ):
        return images

    outputs = (
        history_data.get(
            "outputs",
            {}
        )
    )

    if not isinstance(
        outputs,
        dict
    ):
        return images

    for node_id, node_output in outputs.items():

        if not isinstance(
            node_output,
            dict
        ):
            continue

        node_images = (
            node_output.get(
                "images",
                []
            )
        )

        if not isinstance(
            node_images,
            list
        ):
            continue

        for image_info in node_images:

            if not isinstance(
                image_info,
                dict
            ):
                continue

            filename = (
                image_info.get(
                    "filename"
                )
            )

            if not filename:
                continue

            images.append({

                "filename":
                    filename,

                "subfolder":
                    image_info.get(
                        "subfolder",
                        ""
                    ),

                "type":
                    image_info.get(
                        "type",
                        "output"
                    ),

                "node_id":
                    node_id,

            })

    return images


# ============================================================
# 生成图片
# ============================================================

def generate_comfyui_image(
    positive_prompt,
    negative_prompt
):
    """
    Agent 调用的唯一 ComfyUI 工具。

    参数：
        positive_prompt
        negative_prompt

    返回：
        success
        image_path
        image_paths
    """

    if not isinstance(
        positive_prompt,
        str
    ):

        return {
            "success": False,
            "error":
                "positive_prompt 必须是字符串。",
        }

    if not isinstance(
        negative_prompt,
        str
    ):

        return {
            "success": False,
            "error":
                "negative_prompt 必须是字符串。",
        }

    positive_prompt = (
        positive_prompt.strip()
    )

    negative_prompt = (
        negative_prompt.strip()
    )

    if not positive_prompt:

        return {
            "success": False,
            "error":
                "正面提示词不能为空。",
        }

    if not negative_prompt:

        return {
            "success": False,
            "error":
                "负面提示词不能为空。",
        }

    # ========================================================
    # 构建工作流
    # ========================================================

    workflow = _build_workflow(
        positive_prompt,
        negative_prompt
    )

    client_id = str(
        uuid.uuid4()
    )

    payload = {

        "prompt":
            workflow,

        "client_id":
            client_id,

    }

    # ========================================================
    # 提交 ComfyUI
    # ========================================================

    try:

        response = _http_post_json(
            COMFYUI_URL + "/prompt",
            payload,
            timeout=30
        )

    except urllib.error.URLError as e:

        return {
            "success": False,
            "error":
                "无法连接 ComfyUI："
                + str(e),
        }

    except Exception as e:

        return {
            "success": False,
            "error":
                "提交 ComfyUI 工作流失败："
                + f"{type(e).__name__}: {e}",
        }

    prompt_id = (
        response.get(
            "prompt_id"
        )
    )

    if not prompt_id:

        return {
            "success": False,
            "error":
                "ComfyUI 没有返回 prompt_id。",
            "response":
                response,
        }

    print(
        "[ComfyUI] 已提交任务："
        + str(prompt_id)
    )

    # ========================================================
    # 等待生成
    # ========================================================

    max_wait_seconds = 300

    start_time = time.monotonic()

    history = None

    while True:

        elapsed = (
            time.monotonic()
            - start_time
        )

        if elapsed >= max_wait_seconds:

            return {
                "success": False,
                "error":
                    "ComfyUI 生成超时，"
                    f"已经等待 {max_wait_seconds} 秒。",
                "prompt_id":
                    prompt_id,
            }

        try:

            history_all = _http_get_json(
                COMFYUI_URL
                + "/history/"
                + urllib.parse.quote(
                    str(prompt_id)
                ),
                timeout=30
            )

        except Exception as e:

            print(
                "[ComfyUI] 查询任务状态失败："
                + str(e)
            )

            time.sleep(
                1.0
            )

            continue

        history = (
            history_all.get(
                prompt_id
            )
        )

        if history:

            generated_images = (
                _find_generated_images(
                    history
                )
            )

            if generated_images:

                break

            status = (
                history.get(
                    "status",
                    {}
                )
            )

            status_str = str(
                status
            )

            if (
                "error" in
                status_str.lower()
            ):

                return {
                    "success": False,
                    "error":
                        "ComfyUI 生成失败。",
                    "prompt_id":
                        prompt_id,
                    "status":
                        status,
                }

        time.sleep(
            0.5
        )

    # ========================================================
    # 下载图片
    # ========================================================

    saved_paths = []

    timestamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    for index, image_info in enumerate(
        generated_images,
        1
    ):

        original_filename = (
            image_info["filename"]
        )

        extension = (
            os.path.splitext(
                original_filename
            )[1]
            or ".png"
        )

        save_filename = (
            f"comfyui_"
            f"{timestamp}_"
            f"{index}"
            f"{extension}"
        )

        save_path = os.path.join(
            GENERATED_IMAGE_DIR,
            save_filename
        )

        try:

            _download_image(
                filename=(
                    image_info[
                        "filename"
                    ]
                ),
                subfolder=(
                    image_info[
                        "subfolder"
                    ]
                ),
                image_type=(
                    image_info[
                        "type"
                    ]
                ),
                save_path=save_path,
            )

        except Exception as e:

            return {
                "success": False,
                "error":
                    "生成成功，但下载图片失败："
                    + f"{type(e).__name__}: {e}",
                "prompt_id":
                    prompt_id,
            }

        saved_paths.append(
            save_path
        )

        print(
            "[ComfyUI] 图片已保存："
            + save_path
        )

    # ========================================================
    # 返回
    # ========================================================

    return {

        "success":
            True,

        "message":
            "ComfyUI 图片生成完成。",

        "prompt_id":
            prompt_id,

        "image_path":
            saved_paths[0],

        "image_paths":
            saved_paths,

    }