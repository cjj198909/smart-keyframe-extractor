"""
Azure OpenAI 集成模块
提供与Azure OpenAI Vision API的集成功能
"""

import os
import json
from typing import List, Dict, Optional, Union
import logging
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class AzureOpenAIAnalyzer:
    """Azure OpenAI 视频分析器"""
    
    def __init__(self, 
                 api_key: str = None,
                 endpoint: str = None, 
                 api_version: str = "2024-02-15-preview",
                 deployment_name: str = None):
        """
        初始化Azure OpenAI客户端
        
        Args:
            api_key: Azure OpenAI API密钥
            endpoint: Azure OpenAI端点
            api_version: API版本
            deployment_name: 部署名称 (默认使用环境变量或gpt-4.1-mini)
        """
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = api_version
        # 优先使用环境变量配置的部署名称，否则使用参数，最后默认为gpt-4.1-mini
        self.deployment_name = deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or "gpt-4.1-mini"
        
        if not self.api_key or not self.endpoint:
            raise ValueError("需要提供 Azure OpenAI API密钥和端点")
        
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )
    
    def analyze_video_frames(self, 
                           frames: List[Dict], 
                           custom_prompt: str = None,
                           max_tokens: int = 1000,
                           temperature: float = 0.7,
                           detail: str = "high") -> Dict:
        """
        分析视频关键帧
        
        Args:
            frames: 包含base64数据的帧列表
            custom_prompt: 自定义分析提示
            max_tokens: 最大token数
            temperature: 生成温度
            detail: 图像分析详细程度，可选值: "low", "high", "auto"
        
        Returns:
            分析结果字典
        """
        try:
            # 准备消息
            messages = self._prepare_messages(frames, custom_prompt, detail)
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # 处理响应
            result = {
                'success': True,
                'analysis': response.choices[0].message.content,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'frames_analyzed': len(frames)
            }
            
            logger.info(f"成功分析 {len(frames)} 帧，使用 {response.usage.total_tokens} tokens")
            
            return result
            
        except Exception as e:
            logger.error(f"Azure OpenAI分析失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'frames_analyzed': len(frames)
            }
    
    def _prepare_messages(self, frames: List[Dict], custom_prompt: str = None, detail: str = "high") -> List[Dict]:
        """
        准备Azure OpenAI消息格式
        
        Args:
            frames: 包含base64数据的帧列表
            custom_prompt: 自定义分析提示
            detail: 图像分析详细程度，可选值: "low", "high", "auto"
        
        Returns:
            格式化的消息列表
        """
        # 验证detail参数
        valid_details = ["low", "high", "auto"]
        if detail not in valid_details:
            logger.warning(f"无效的detail参数: {detail}，使用默认值 'high'")
            detail = "high"
        
        messages = []
        
        # 系统提示
        system_prompt = """你是一个专业的视频内容分析师。请仔细分析提供的视频关键帧，并提供详细的分析报告。
        
分析应包括：
1. 场景描述：每一帧的主要内容和场景
2. 时间流程：帧与帧之间的时间关系和内容变化
3. 主要对象：识别视频中的重要对象、人物或元素
4. 动作分析：描述可能的动作或变化趋势
5. 整体总结：对整个视频内容的概括性描述

请用中文回答，并保持专业和详细。"""
        
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # 用户消息
        content = []
        
        # 添加文本说明
        prompt_text = custom_prompt or f"请分析这 {len(frames)} 张视频关键帧。这些帧按时间顺序排列，代表了视频中的关键时刻。"
        
        content.append({
            "type": "text",
            "text": prompt_text
        })
        
        # 添加图像
        for i, frame in enumerate(frames):
            if 'base64' in frame:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{frame['base64']}",
                        "detail": detail
                    }
                })
                
                # 添加帧的时间信息
                content.append({
                    "type": "text", 
                    "text": f"帧 {i+1}: 时间 {frame.get('timestamp', 0):.1f}秒"
                })
        
        messages.append({
            "role": "user",
            "content": content
        })
        
        return messages
    
    def batch_analyze_videos(self, video_results: List[Dict], **kwargs) -> List[Dict]:
        """
        批量分析多个视频的关键帧
        
        Args:
            video_results: 多个视频的提取结果列表
            **kwargs: 传递给analyze_video_frames的参数
        
        Returns:
            批量分析结果列表
        """
        results = []
        
        for i, video_result in enumerate(video_results):
            if 'frames' in video_result and video_result['frames']:
                logger.info(f"分析第 {i+1}/{len(video_results)} 个视频...")
                
                analysis = self.analyze_video_frames(video_result['frames'], **kwargs)
                analysis['video_path'] = video_result.get('video_path', f'video_{i+1}')
                analysis['video_duration'] = video_result.get('video_duration', 0)
                
                results.append(analysis)
            else:
                logger.warning(f"第 {i+1} 个视频没有有效的关键帧")
                results.append({
                    'success': False,
                    'error': '没有有效的关键帧',
                    'video_path': video_result.get('video_path', f'video_{i+1}')
                })
        
        return results


def analyze_video_with_azure_openai(video_path: str,
                                   api_key: str = None,
                                   endpoint: str = None,
                                   k: Union[int, str] = 5,
                                   resolution: str = '720p',
                                   custom_prompt: str = None,
                                   detail: str = "high",
                                   **extract_kwargs) -> Dict:
    """
    完整的视频分析流程：提取关键帧 + Azure OpenAI分析
    
    Args:
        video_path: 视频文件路径
        api_key: Azure OpenAI API密钥
        endpoint: Azure OpenAI端点
        k: 要提取的关键帧数量
        resolution: 输出分辨率
        custom_prompt: 自定义分析提示
        detail: 图像分析详细程度，可选值: "low", "high", "auto"
        **extract_kwargs: 传递给extract_top_k_keyframes的其他参数
    
    Returns:
        包含关键帧提取和AI分析结果的字典
    """
    from .extractor import extract_top_k_keyframes
    
    logger.info(f"开始完整视频分析流程: {video_path}")
    
    # 1. 提取关键帧
    logger.info("步骤 1/2: 提取视频关键帧...")
    extract_result = extract_top_k_keyframes(
        video_path=video_path,
        k=k,
        resolution=resolution,
        return_base64=True,
        save_files=False,
        **extract_kwargs
    )
    
    if 'error' in extract_result:
        return {
            'success': False,
            'error': f"关键帧提取失败: {extract_result['error']}",
            'stage': 'keyframe_extraction'
        }
    
    # 2. Azure OpenAI分析
    logger.info("步骤 2/2: Azure OpenAI分析...")
    try:
        analyzer = AzureOpenAIAnalyzer(api_key=api_key, endpoint=endpoint)
        analysis_result = analyzer.analyze_video_frames(
            frames=extract_result['frames'],
            custom_prompt=custom_prompt,
            detail=detail
        )
        
        # 合并结果
        final_result = {
            'success': analysis_result['success'],
            'video_analysis': analysis_result,
            'keyframe_extraction': extract_result,
            'total_processing_time': None  # 可以添加时间统计
        }
        
        if analysis_result['success']:
            logger.info("视频分析完成!")
        else:
            logger.error(f"AI分析失败: {analysis_result.get('error', '未知错误')}")
        
        return final_result
        
    except Exception as e:
        logger.error(f"Azure OpenAI分析过程出错: {e}")
        return {
            'success': False,
            'error': f"AI分析失败: {str(e)}",
            'stage': 'ai_analysis',
            'keyframe_extraction': extract_result  # 保留关键帧提取结果
        }
