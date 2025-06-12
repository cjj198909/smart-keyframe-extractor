"""
视觉处理工具 - 参考 qwen-vl-utils 的设计
支持图像和视频的智能处理，包括分辨率调整和格式转换
"""

from __future__ import annotations

import base64
import math
import warnings
from io import BytesIO
from typing import Union, List, Dict, Tuple, Optional

import requests
import numpy as np
from PIL import Image


# 图像处理常量
IMAGE_FACTOR = 28
MIN_PIXELS = 4 * 28 * 28
MAX_PIXELS = 16384 * 28 * 28
MAX_RATIO = 200

# 视频处理常量
VIDEO_MIN_PIXELS = 128 * 28 * 28
VIDEO_MAX_PIXELS = 768 * 28 * 28
VIDEO_TOTAL_PIXELS = 24576 * 28 * 28
FRAME_FACTOR = 2
FPS = 2.0
FPS_MIN_FRAMES = 4
FPS_MAX_FRAMES = 768


def round_by_factor(number: int, factor: int) -> int:
    """返回最接近 'number' 且能被 'factor' 整除的整数"""
    return round(number / factor) * factor


def ceil_by_factor(number: int, factor: int) -> int:
    """返回大于等于 'number' 且能被 'factor' 整除的最小整数"""
    return math.ceil(number / factor) * factor


def floor_by_factor(number: int, factor: int) -> int:
    """返回小于等于 'number' 且能被 'factor' 整除的最大整数"""
    return math.floor(number / factor) * factor


def smart_resize(
    height: int, 
    width: int, 
    factor: int = IMAGE_FACTOR, 
    min_pixels: int = MIN_PIXELS, 
    max_pixels: int = MAX_PIXELS
) -> tuple[int, int]:
    """
    智能调整图像尺寸，满足以下条件：
    
    1. 高度和宽度都能被 'factor' 整除
    2. 总像素数在 ['min_pixels', 'max_pixels'] 范围内
    3. 尽可能保持原始宽高比
    """
    if max(height, width) / min(height, width) > MAX_RATIO:
        raise ValueError(
            f"绝对宽高比必须小于 {MAX_RATIO}，当前为 {max(height, width) / min(height, width)}"
        )
    
    h_bar = max(factor, round_by_factor(height, factor))
    w_bar = max(factor, round_by_factor(width, factor))
    
    if h_bar * w_bar > max_pixels:
        beta = math.sqrt((height * width) / max_pixels)
        h_bar = floor_by_factor(height / beta, factor)
        w_bar = floor_by_factor(width / beta, factor)
    elif h_bar * w_bar < min_pixels:
        beta = math.sqrt(min_pixels / (height * width))
        h_bar = ceil_by_factor(height * beta, factor)
        w_bar = ceil_by_factor(width * beta, factor)
    
    return h_bar, w_bar


def fetch_image(ele: dict[str, str | Image.Image], size_factor: int = IMAGE_FACTOR) -> Image.Image:
    """
    获取并处理图像
    
    Args:
        ele: 包含图像信息的字典
        size_factor: 尺寸因子
    
    Returns:
        处理后的PIL图像对象
    """
    if "image" in ele:
        image = ele["image"]
    else:
        image = ele["image_url"]
    
    image_obj = None
    
    if isinstance(image, Image.Image):
        image_obj = image
    elif image.startswith("http://") or image.startswith("https://"):
        response = requests.get(image, stream=True)
        response.raise_for_status()
        image_obj = Image.open(response.raw)
    elif image.startswith("file://"):
        image_obj = Image.open(image[7:])
    elif image.startswith("data:image"):
        data = image.split(";", 1)[1]
        if data.startswith("base64,"):
            data = base64.b64decode(data[7:])
            image_obj = Image.open(BytesIO(data))
    else:
        image_obj = Image.open(image)
    
    if image_obj is None:
        raise ValueError(f"无法识别的图像输入，支持本地路径、HTTP URL、base64和PIL.Image，输入: {image}")
    
    image = image_obj.convert("RGB")
    
    # 调整尺寸
    if "resized_height" in ele and "resized_width" in ele:
        resized_height, resized_width = smart_resize(
            ele["resized_height"],
            ele["resized_width"],
            factor=size_factor,
        )
    else:
        width, height = image.size
        min_pixels = ele.get("min_pixels", MIN_PIXELS)
        max_pixels = ele.get("max_pixels", MAX_PIXELS)
        resized_height, resized_width = smart_resize(
            height,
            width,
            factor=size_factor,
            min_pixels=min_pixels,
            max_pixels=max_pixels,
        )
    
    image = image.resize((resized_width, resized_height))
    return image


def image_to_base64(image: Union[Image.Image, str], format: str = "JPEG", quality: int = 95) -> str:
    """
    将图像转换为base64编码
    
    Args:
        image: PIL图像对象或图像文件路径
        format: 输出格式 (JPEG, PNG等)
        quality: JPEG质量 (1-100)
    
    Returns:
        base64编码的字符串
    """
    if isinstance(image, str):
        image = Image.open(image)
    
    if image.mode != 'RGB' and format.upper() == 'JPEG':
        image = image.convert('RGB')
    
    buffer = BytesIO()
    save_kwargs = {'format': format, 'optimize': True}
    if format.upper() == 'JPEG':
        save_kwargs['quality'] = quality
    
    image.save(buffer, **save_kwargs)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str


def base64_to_image(base64_str: str) -> Image.Image:
    """
    将base64编码转换为PIL图像对象
    
    Args:
        base64_str: base64编码的图像字符串
    
    Returns:
        PIL图像对象
    """
    # 如果包含data URL前缀，去除它
    if base64_str.startswith('data:image'):
        base64_str = base64_str.split(',', 1)[1]
    
    image_data = base64.b64decode(base64_str)
    image = Image.open(BytesIO(image_data))
    return image


def extract_vision_info(conversations: list[dict] | list[list[dict]]) -> list[dict]:
    """
    从对话中提取视觉信息
    
    Args:
        conversations: 对话数据
    
    Returns:
        视觉信息列表
    """
    vision_infos = []
    if isinstance(conversations[0], dict):
        conversations = [conversations]
    
    for conversation in conversations:
        for message in conversation:
            if isinstance(message["content"], list):
                for ele in message["content"]:
                    if (
                        "image" in ele
                        or "image_url" in ele
                        or "video" in ele
                        or ele.get("type") in ("image", "image_url", "video")
                    ):
                        vision_infos.append(ele)
    return vision_infos


def process_vision_info(
    conversations: list[dict] | list[list[dict]],
) -> tuple[list[Image.Image] | None, list[dict] | None]:
    """
    处理视觉信息
    
    Args:
        conversations: 对话数据
    
    Returns:
        (图像列表, 视频信息列表) 元组
    """
    vision_infos = extract_vision_info(conversations)
    
    # 读取图像或视频
    image_inputs = []
    video_inputs = []
    
    for vision_info in vision_infos:
        if "image" in vision_info or "image_url" in vision_info:
            image_inputs.append(fetch_image(vision_info))
        elif "video" in vision_info:
            video_inputs.append(vision_info)
        else:
            raise ValueError("content中应包含image、image_url或video")
    
    if len(image_inputs) == 0:
        image_inputs = None
    if len(video_inputs) == 0:
        video_inputs = None
    
    return image_inputs, video_inputs


def prepare_azure_openai_messages(frames: List[Dict], system_prompt: str = None) -> List[Dict]:
    """
    为Azure OpenAI准备消息格式
    
    Args:
        frames: 包含base64数据的帧列表
        system_prompt: 系统提示（可选）
    
    Returns:
        Azure OpenAI消息列表
    """
    messages = []
    
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    # 构建用户消息
    content = []
    
    # 添加文本说明
    content.append({
        "type": "text",
        "text": f"请分析这 {len(frames)} 张视频关键帧，并描述视频内容的变化和主要情节。"
    })
    
    # 添加图像
    for i, frame in enumerate(frames):
        if 'base64' in frame:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{frame['base64']}",
                    "detail": "high"
                }
            })
    
    messages.append({
        "role": "user", 
        "content": content
    })
    
    return messages


def calculate_token_usage(frames: List[Dict], resolution: str = "high") -> Dict:
    """
    估算Azure OpenAI的token使用量
    
    Args:
        frames: 帧列表
        resolution: 图像分辨率设置 ("low" 或 "high")
    
    Returns:
        token使用量估算
    """
    # Azure OpenAI GPT-4V的token计算规则（近似值）
    base_tokens = 85  # 基础token
    
    if resolution == "low":
        tokens_per_image = 85
    else:  # high resolution
        tokens_per_image = 170  # 平均值，实际根据图像尺寸计算
    
    total_image_tokens = len(frames) * tokens_per_image
    total_tokens = base_tokens + total_image_tokens
    
    return {
        "total_tokens": total_tokens,
        "base_tokens": base_tokens,
        "image_tokens": total_image_tokens,
        "images_count": len(frames),
        "resolution": resolution
    }
