"""
Smart Keyframe Extractor - 智能视频关键帧提取工具
支持自适应视频时长，可按固定时间间隔自动计算帧数，支持分辨率选择，返回base64编码用于AI分析
"""

from .extractor import SmartKeyFrameExtractor, extract_top_k_keyframes
from .vision_utils import (
    process_vision_info, 
    smart_resize, 
    fetch_image, 
    image_to_base64,
    base64_to_image,
    prepare_azure_openai_messages,
    calculate_token_usage
)

# Azure OpenAI集成（可选导入）
try:
    from .azure_openai import AzureOpenAIAnalyzer, analyze_video_with_azure_openai
    _has_azure = True
except ImportError:
    _has_azure = False
    AzureOpenAIAnalyzer = None
    analyze_video_with_azure_openai = None

__version__ = "0.1.0"
__author__ = "jiajunchen"
__email__ = "your-email@example.com"

__all__ = [
    "SmartKeyFrameExtractor",
    "extract_top_k_keyframes", 
    "process_vision_info",
    "smart_resize",
    "fetch_image",
    "image_to_base64",
    "base64_to_image",
    "prepare_azure_openai_messages",
    "calculate_token_usage"
]

# 只有在成功导入Azure相关模块时才添加到__all__
if _has_azure:
    __all__.extend([
        "AzureOpenAIAnalyzer",
        "analyze_video_with_azure_openai"
    ])
