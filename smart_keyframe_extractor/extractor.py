#!/usr/bin/env python3
"""
智能视频关键帧提取工具 - 增强版
支持自适应视频时长，可按固定时间间隔自动计算帧数，支持分辨率选择
返回base64编码用于Azure OpenAI分析
"""

import subprocess
import json
import os
import base64
import numpy as np
from PIL import Image
import cv2
import tempfile
from typing import List, Dict, Tuple, Optional, Union
import shutil
import sys
import logging
from pathlib import Path
import heapq
from io import BytesIO

# 导入远程视频支持
try:
    from .remote_video_utils import (
        RemoteVideoDownloader, 
        is_remote_url, 
        get_video_url_info
    )
    HAS_REMOTE_SUPPORT = True
except ImportError:
    HAS_REMOTE_SUPPORT = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmartKeyFrameExtractor:
    """智能关键帧提取器 - 支持base64输出和远程视频"""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe", 
                 enable_remote: bool = True, cache_dir: Optional[str] = None):
        """
        初始化智能关键帧提取器
        
        Args:
            ffmpeg_path: FFmpeg可执行文件路径
            ffprobe_path: FFprobe可执行文件路径  
            enable_remote: 是否启用远程视频支持
            cache_dir: 远程视频缓存目录
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.enable_remote = enable_remote
        
        # 初始化远程视频下载器
        if self.enable_remote and HAS_REMOTE_SUPPORT:
            self.remote_downloader = RemoteVideoDownloader(cache_dir=cache_dir)
        else:
            self.remote_downloader = None
            
        self._check_installations()
    
    def _check_installations(self):
        """检查依赖"""
        try:
            subprocess.run([self.ffmpeg_path, '-version'], capture_output=True, check=True)
            subprocess.run([self.ffprobe_path, '-version'], capture_output=True, check=True)
            import cv2
        except:
            raise RuntimeError("请确保安装了 FFmpeg 和 opencv-python")
    
    def get_video_info(self, video_path: str) -> Optional[Dict]:
        """获取视频信息"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return None
        
        info = {
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        }
        info['duration'] = info['total_frames'] / info['fps'] if info['fps'] > 0 else 0
        
        cap.release()
        return info
    
    def _prepare_video_path(self, video_path: str, use_cache: bool = True) -> Tuple[str, bool]:
        """
        准备视频路径，如果是远程URL则下载到本地
        
        Args:
            video_path: 视频路径或URL
            use_cache: 是否使用缓存
            
        Returns:
            (local_path, is_temporary) - 本地路径和是否为临时文件的标志
        """
        # 检查是否为远程URL
        if not is_remote_url(video_path):
            return video_path, False
        
        # 检查远程支持
        if not self.enable_remote or not self.remote_downloader:
            if not HAS_REMOTE_SUPPORT:
                raise RuntimeError(
                    "远程视频功能不可用。请安装必要的依赖:\n"
                    "pip install requests boto3 azure-storage-blob google-cloud-storage"
                )
            else:
                raise RuntimeError("远程视频功能已禁用。请在初始化时设置 enable_remote=True")
        
        # 获取URL信息
        url_info = get_video_url_info(video_path)
        logger.info(f"检测到远程视频: {url_info['storage_type']} - {video_path}")
        
        # 下载视频
        local_path = self.remote_downloader.download_video(video_path, use_cache=use_cache)
        if local_path is None:
            raise RuntimeError(f"下载远程视频失败: {video_path}")
        
        # 返回本地路径和临时文件标志
        is_temporary = not use_cache
        return local_path, is_temporary
    
    def get_resolution_params(self, resolution: str, original_width: int, original_height: int) -> Tuple[Optional[str], Optional[str]]:
        """
        根据分辨率选项返回FFmpeg的scale参数
        
        Args:
            resolution: 分辨率选项 ('original', '1080p', '720p', '480p', '360p', '240p')
            original_width: 原始视频宽度
            original_height: 原始视频高度
        
        Returns:
            (scale_filter, scale_params) 元组
        """
        if resolution == 'original':
            return None, None
        
        # 预定义的分辨率
        resolution_map = {
            '1080p': (1920, 1080),
            '720p': (1280, 720),
            '480p': (854, 480),
            '360p': (640, 360),
            '240p': (426, 240)
        }
        
        if resolution not in resolution_map:
            logger.warning(f"未知分辨率 '{resolution}'，使用原始分辨率")
            return None, None
        
        target_width, target_height = resolution_map[resolution]
        
        # 计算缩放比例，保持宽高比
        scale_ratio = min(target_width / original_width, target_height / original_height)
        
        # 如果原始分辨率已经小于或等于目标分辨率，不进行缩放
        if scale_ratio >= 1.0:
            logger.info(f"原始分辨率 ({original_width}x{original_height}) 已小于等于目标分辨率 {resolution}，保持原始分辨率")
            return None, None
        
        # 计算实际输出尺寸（保持宽高比，确保是偶数）
        new_width = int((original_width * scale_ratio) // 2) * 2
        new_height = int((original_height * scale_ratio) // 2) * 2
        
        scale_filter = f"scale={new_width}:{new_height}"
        
        logger.info(f"分辨率调整: {original_width}x{original_height} -> {new_width}x{new_height} ({resolution})")
        
        return scale_filter, f"{new_width}x{new_height}"
    
    def calculate_adaptive_frame_count(self, duration: float, mode: str = "fixed", 
                                     interval: float = 10.0, frames_per_interval: int = 1,
                                     min_frames: int = 3, max_frames: int = 30) -> int:
        """
        根据视频时长自适应计算需要提取的帧数
        
        Args:
            duration: 视频时长（秒）
            mode: 模式 - "fixed"(固定数量), "adaptive"(自适应), "interval"(按间隔)
            interval: 时间间隔（秒）
            frames_per_interval: 每个时间间隔提取的帧数
            min_frames: 最小帧数
            max_frames: 最大帧数
        
        Returns:
            计算出的帧数
        """
        if mode == "fixed":
            # 固定模式：直接返回指定数量
            return min(max(frames_per_interval, min_frames), max_frames)
        
        elif mode == "interval":
            # 间隔模式：每X秒提取Y帧
            intervals = duration / interval
            calculated_frames = int(intervals * frames_per_interval)
            
        elif mode == "adaptive":
            # 自适应模式：根据视频长度动态调整
            if duration <= 30:  # 短视频（<=30秒）
                calculated_frames = min(5, int(duration / 5))  # 约每5秒1帧
            elif duration <= 60:  # 中等视频（30-60秒）
                calculated_frames = min(8, int(duration / 7))  # 约每7秒1帧
            elif duration <= 300:  # 较长视频（1-5分钟）
                calculated_frames = min(15, int(duration / 15))  # 约每15秒1帧
            else:  # 长视频（>5分钟）
                calculated_frames = min(20, int(duration / 20))  # 约每20秒1帧
        
        else:
            raise ValueError(f"未知模式: {mode}")
        
        # 确保在合理范围内
        final_count = min(max(calculated_frames, min_frames), max_frames)
        
        logger.info(f"自适应计算结果: 视频时长 {duration:.1f}秒, "
                   f"模式 '{mode}', 计算帧数 {final_count}")
        
        return final_count
    
    def compute_frame_changes(self, video_path: str, sample_rate: int = 1) -> Tuple[List[Dict], Dict]:
        """计算所有帧的变化分数"""
        
        cap = cv2.VideoCapture(video_path)
        video_info = self.get_video_info(video_path)
        
        if not video_info:
            return [], {}
        
        logger.info(f"视频信息: {video_info['total_frames']} 帧, "
                   f"{video_info['fps']:.2f} fps, {video_info['duration']:.2f} 秒")
        
        # 降采样参数
        scale_factor = 0.25  # 降低分辨率以加快处理
        
        # 读取第一帧
        ret, first_frame = cap.read()
        if not ret:
            cap.release()
            return [], {}
        
        # 降低分辨率
        first_frame_small = cv2.resize(first_frame, None, fx=scale_factor, fy=scale_factor)
        prev_gray = cv2.cvtColor(first_frame_small, cv2.COLOR_BGR2GRAY)
        
        # 存储帧变化信息
        frame_changes = []
        
        # 第一帧
        frame_changes.append({
            'frame_idx': 0,
            'timestamp': 0.0,
            'change_score': 0.0,  # 第一帧没有变化
            'scene_score': 0.0,
            'motion_score': 0.0,
            'color_score': 0.0
        })
        
        # 光流参数
        flow_params = dict(
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0
        )
        
        frame_count = 0
        prev_hsv = cv2.cvtColor(first_frame_small, cv2.COLOR_BGR2HSV)
        
        while True:
            # 采样读取
            for _ in range(sample_rate):
                ret = cap.grab()
                if not ret:
                    break
                frame_count += 1
            
            if not ret:
                break
            
            ret, frame = cap.retrieve()
            if not ret:
                break
            
            # 降低分辨率
            frame_small = cv2.resize(frame, None, fx=scale_factor, fy=scale_factor)
            curr_gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
            curr_hsv = cv2.cvtColor(frame_small, cv2.COLOR_BGR2HSV)
            
            # 1. 计算光流 (运动分数)
            try:
                flow = cv2.calcOpticalFlowFarneback(prev_gray, curr_gray, None, **flow_params)
                magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                motion_score = np.mean(magnitude) * 10  # 放大系数
            except:
                motion_score = 0.0
            
            # 2. 计算像素差异 (场景变化分数)
            pixel_diff = cv2.absdiff(prev_gray, curr_gray)
            scene_score = np.mean(pixel_diff)
            
            # 3. 计算颜色直方图差异
            hist_prev = cv2.calcHist([prev_hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            hist_curr = cv2.calcHist([curr_hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            hist_prev = cv2.normalize(hist_prev, hist_prev).flatten()
            hist_curr = cv2.normalize(hist_curr, hist_curr).flatten()
            color_score = cv2.compareHist(hist_prev, hist_curr, cv2.HISTCMP_CHISQR)
            
            # 4. 边缘变化分数
            edges_prev = cv2.Canny(prev_gray, 50, 150)
            edges_curr = cv2.Canny(curr_gray, 50, 150)
            edge_diff = cv2.absdiff(edges_prev, edges_curr)
            edge_score = np.sum(edge_diff) / (edge_diff.shape[0] * edge_diff.shape[1]) * 100
            
            # 综合变化分数
            total_score = (
                motion_score * 2.0 +      # 运动权重最高
                scene_score * 1.5 +       # 场景变化次之
                color_score * 0.5 +       # 颜色变化
                edge_score * 1.0          # 边缘变化
            )
            
            frame_changes.append({
                'frame_idx': frame_count,
                'timestamp': frame_count / video_info['fps'],
                'change_score': total_score,
                'scene_score': scene_score,
                'motion_score': motion_score,
                'color_score': color_score,
                'edge_score': edge_score
            })
            
            # 更新前一帧
            prev_gray = curr_gray
            prev_hsv = curr_hsv
            
            # 进度提示
            if frame_count % 50 == 0:
                logger.info(f"已分析 {frame_count}/{video_info['total_frames']} 帧...")
        
        cap.release()
        
        logger.info(f"帧分析完成，共计算了 {len(frame_changes)} 帧的变化分数")
        
        return frame_changes, video_info
    
    def select_global_top_k_frames(self, frame_changes: List[Dict], k: int) -> List[Dict]:
        """选择全局变化最大的K帧，同时考虑多样性"""
        
        if len(frame_changes) <= k:
            return frame_changes
        
        # 1. 首先按变化分数排序
        sorted_frames = sorted(frame_changes, key=lambda x: x['change_score'], reverse=True)
        
        # 2. 使用贪心算法选择既有高分又有多样性的帧
        selected_frames = []
        
        # 始终包含第一帧（提供上下文）
        selected_frames.append(frame_changes[0])
        k -= 1
        
        # 最小时间间隔（秒）- 根据总帧数动态调整
        total_duration = frame_changes[-1]['timestamp']
        # 防止k为0的除零错误
        divisor = max(k * 3, 1)
        min_time_interval = max(0.5, total_duration / divisor)  # 动态计算
        
        # 选择剩余的帧
        for frame in sorted_frames:
            if len(selected_frames) >= k + 1:  # +1 因为已经有第一帧
                break
            
            # 检查时间间隔
            too_close = False
            for selected in selected_frames:
                if abs(frame['timestamp'] - selected['timestamp']) < min_time_interval:
                    too_close = True
                    break
            
            if not too_close and frame not in selected_frames:
                selected_frames.append(frame)
        
        # 如果还没选够（时间间隔限制太严），放宽限制
        if len(selected_frames) < k + 1:
            min_time_interval = max(0.2, total_duration / (k * 5))  # 进一步放宽
            
            for frame in sorted_frames:
                if len(selected_frames) >= k + 1:
                    break
                
                if frame not in selected_frames:
                    too_close = False
                    for selected in selected_frames:
                        if abs(frame['timestamp'] - selected['timestamp']) < min_time_interval:
                            too_close = True
                            break
                    
                    if not too_close:
                        selected_frames.append(frame)
        
        # 按时间排序
        selected_frames.sort(key=lambda x: x['timestamp'])
        
        # 输出选中帧的信息
        logger.info("\n选中的关键帧:")
        for i, frame in enumerate(selected_frames):
            logger.info(f"  帧 {frame['frame_idx']} "
                       f"(时间: {frame['timestamp']:.2f}s, "
                       f"总分: {frame['change_score']:.2f}, "
                       f"运动: {frame['motion_score']:.2f}, "
                       f"场景: {frame['scene_score']:.2f})")
        
        return selected_frames
    
    def image_to_base64(self, image_path: str, quality: int = 95) -> str:
        """将图像文件转换为base64编码"""
        try:
            with Image.open(image_path) as img:
                # 转换为RGB模式（如果需要）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 压缩并转换为base64
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
                img_str = base64.b64encode(buffer.getvalue()).decode()
                return img_str
        except Exception as e:
            logger.error(f"转换图像到base64失败: {e}")
            return ""
    
    def extract_frames_with_ffmpeg(self, video_path: str, frame_info_list: List[Dict], 
                                  output_dir: str = None, resolution: str = 'original',
                                  return_base64: bool = True, save_files: bool = False) -> List[Dict]:
        """使用FFmpeg提取指定帧，支持base64输出"""
        
        # 如果需要保存文件但没有指定输出目录，创建临时目录
        if save_files and output_dir is None:
            output_dir = tempfile.mkdtemp(prefix='keyframes_')
            logger.info(f"创建临时目录: {output_dir}")
        elif save_files:
            os.makedirs(output_dir, exist_ok=True)
            # 清空目录
            for file in os.listdir(output_dir):
                if file.endswith(('.jpg', '.png')):
                    os.unlink(os.path.join(output_dir, file))
        
        # 获取视频信息用于分辨率计算
        video_info = self.get_video_info(video_path)
        if not video_info:
            logger.error("无法获取视频信息")
            return []
        
        # 计算分辨率参数
        scale_filter, resolution_info = self.get_resolution_params(
            resolution, video_info['width'], video_info['height']
        )
        
        saved_frames = []
        
        for idx, frame_info in enumerate(frame_info_list):
            timestamp = frame_info['timestamp']
            
            # 创建临时文件用于FFmpeg输出
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # 构建FFmpeg命令
            cmd = [
                self.ffmpeg_path,
                '-ss', str(timestamp),
                '-i', video_path,
                '-frames:v', '1',
                '-q:v', '2'
            ]
            
            # 添加分辨率缩放参数
            if scale_filter:
                cmd.extend(['-vf', scale_filter])
            
            cmd.extend(['-y', temp_path])
            
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                
                if os.path.exists(temp_path):
                    frame_data = {
                        'frame_idx': frame_info['frame_idx'],
                        'timestamp': timestamp,
                        'change_score': frame_info['change_score'],
                        'motion_score': frame_info['motion_score'],
                        'scene_score': frame_info['scene_score'],
                        'resolution': resolution_info if resolution_info else f"{video_info['width']}x{video_info['height']}"
                    }
                    
                    # 转换为base64
                    if return_base64:
                        base64_data = self.image_to_base64(temp_path)
                        frame_data['base64'] = base64_data
                        frame_data['format'] = 'jpeg'
                    
                    # 保存文件（如果需要）
                    if save_files and output_dir:
                        output_filename = f'keyframe-{idx+1:03d}.jpg'
                        output_path = os.path.join(output_dir, output_filename)
                        shutil.copy2(temp_path, output_path)
                        frame_data['path'] = output_path
                        frame_data['filename'] = output_filename
                        logger.info(f"已保存: {output_filename} ({frame_data['resolution']})")
                    
                    saved_frames.append(frame_data)
                    
                # 清理临时文件
                os.unlink(temp_path)
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"提取帧失败: 时间 {timestamp:.2f}s, 错误: {e}")
                # 清理临时文件
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        
        return saved_frames


def extract_top_k_keyframes(video_path: str, output_dir: str = None, 
                           k: Union[int, str] = 5,
                           adaptive_mode: str = None,
                           interval: float = 10.0,
                           frames_per_interval: int = 1,
                           min_frames: int = 3,
                           max_frames: int = 30,
                           resolution: str = 'original',
                           return_base64: bool = True,
                           save_files: bool = False) -> Dict:
    """
    主函数：提取视频中变化最大的K帧，支持base64输出
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录（可选，当save_files=True时使用）
        k: 帧数 - 可以是具体数字或 "auto" 自动计算
        adaptive_mode: 自适应模式 - "fixed", "adaptive", "interval"
        interval: 时间间隔（秒）
        frames_per_interval: 每个间隔的帧数
        min_frames: 最小帧数
        max_frames: 最大帧数
        resolution: 输出分辨率 - "original", "1080p", "720p", "480p", "360p", "240p"
        return_base64: 是否返回base64编码
        save_files: 是否保存文件到磁盘
    """
    
    logger.info(f"\n{'='*60}")
    logger.info(f"开始处理视频: {video_path}")
    logger.info(f"输出分辨率: {resolution}")
    logger.info(f"返回base64: {return_base64}")
    logger.info(f"保存文件: {save_files}")
    
    extractor = SmartKeyFrameExtractor(enable_remote=True)
    
    # 准备视频路径（支持远程URL）
    try:
        prepared_video_path, is_temporary = extractor._prepare_video_path(video_path)
    except Exception as e:
        return {'error': f'视频准备失败: {str(e)}'}
    
    # 1. 分析所有帧的变化
    logger.info("步骤 1/3: 分析视频帧变化...")
    frame_changes, video_info = extractor.compute_frame_changes(prepared_video_path, sample_rate=1)
    
    if not frame_changes:
        return {'error': '无法分析视频'}
    
    # 2. 确定要提取的帧数
    if k == "auto" or adaptive_mode is not None:
        # 自动计算帧数
        mode = adaptive_mode or "adaptive"
        k_calculated = extractor.calculate_adaptive_frame_count(
            video_info['duration'], 
            mode=mode,
            interval=interval,
            frames_per_interval=frames_per_interval,
            min_frames=min_frames,
            max_frames=max_frames
        )
        logger.info(f"自动计算提取帧数: {k_calculated}")
    else:
        k_calculated = int(k)
        logger.info(f"指定提取帧数: {k_calculated}")
    
    logger.info(f"{'='*60}\n")
    
    # 3. 选择变化最大的K帧
    logger.info(f"步骤 2/3: 从 {len(frame_changes)} 帧中选择变化最大的 {k_calculated} 帧...")
    selected_frames = extractor.select_global_top_k_frames(frame_changes, k_calculated)
    
    # 4. 提取高质量帧（包含分辨率调整和base64编码）
    logger.info(f"\n步骤 3/3: 提取高质量关键帧...")
    saved_frames = extractor.extract_frames_with_ffmpeg(
        prepared_video_path, selected_frames, output_dir, resolution,
        return_base64=return_base64, save_files=save_files
    )
    
    # 生成分析报告
    result = {
        'video_path': video_path,
        'video_duration': video_info['duration'],
        'total_frames_analyzed': len(frame_changes),
        'requested_frames': k,
        'calculated_frames': k_calculated,
        'extracted_frames': len(saved_frames),
        'adaptive_mode': adaptive_mode or 'fixed',
        'resolution': resolution,
        'original_resolution': f"{video_info['width']}x{video_info['height']}",
        'output_dir': output_dir,
        'return_base64': return_base64,
        'save_files': save_files,
        'frames': saved_frames,
        'statistics': {
            'max_change_score': max(f['change_score'] for f in frame_changes),
            'avg_change_score': np.mean([f['change_score'] for f in frame_changes]),
            'selected_total_score': sum(f['change_score'] for f in saved_frames)
        }
    }
    
    # 输出总结
    logger.info(f"\n{'='*60}")
    logger.info("提取完成!")
    logger.info(f"视频时长: {video_info['duration']:.1f} 秒")
    logger.info(f"原始分辨率: {result['original_resolution']}")
    logger.info(f"输出分辨率: {resolution}")
    logger.info(f"分析帧数: {result['total_frames_analyzed']}")
    logger.info(f"提取帧数: {result['extracted_frames']}")
    logger.info(f"提取模式: {result['adaptive_mode']}")
    logger.info(f"返回base64: {return_base64}")
    logger.info(f"保存文件: {save_files}")
    logger.info(f"最大变化分数: {result['statistics']['max_change_score']:.2f}")
    logger.info(f"平均变化分数: {result['statistics']['avg_change_score']:.2f}")
    logger.info(f"\n关键帧摘要:")
    
    for i, frame in enumerate(saved_frames):
        base64_info = f", base64长度 {len(frame.get('base64', ''))}" if return_base64 else ""
        file_info = f", 文件 {frame.get('filename', 'N/A')}" if save_files else ""
        logger.info(f"  - 帧 {i+1}: "
                   f"时间 {frame['timestamp']:.1f}s, "
                   f"变化分数 {frame['change_score']:.1f}, "
                   f"分辨率 {frame.get('resolution', 'N/A')}"
                   f"{base64_info}{file_info}")
    
    if output_dir and save_files:
        logger.info(f"\n输出目录: {output_dir}")
    logger.info(f"{'='*60}\n")
    
    # 清理临时文件（如果有）
    if is_temporary and os.path.exists(prepared_video_path):
        try:
            if extractor.remote_downloader:
                extractor.remote_downloader.cleanup_temp_file(prepared_video_path)
            else:
                os.unlink(prepared_video_path)
            logger.info(f"已清理临时文件: {prepared_video_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
    
    return result


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='智能视频关键帧提取工具（支持自适应模式、分辨率选择和base64输出）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 固定提取5帧，720p分辨率，输出base64
  python %(prog)s video.mp4 -k 5 --resolution 720p --base64
  
  # 自适应模式，480p分辨率，同时保存文件和base64
  python %(prog)s video.mp4 -o output_frames -k auto --resolution 480p --base64 --save-files
  
  # 每10秒提取1帧，原始分辨率，仅输出base64
  python %(prog)s video.mp4 --mode interval --interval 10 --frames-per-interval 1 --base64
  
  # 每5秒提取2帧，最少3帧，最多20帧，360p分辨率，保存文件
  python %(prog)s video.mp4 -o output_frames --mode interval --interval 5 --frames-per-interval 2 --min-frames 3 --max-frames 20 --resolution 360p --save-files
        """
    )
    
    parser.add_argument('input', help='视频文件路径')
    parser.add_argument('-o', '--output', help='输出目录（当--save-files时必需）')
    parser.add_argument('-k', '--keyframes', default='5',
                       help='要提取的关键帧数量，可以是数字或 "auto"')
    parser.add_argument('--mode', choices=['fixed', 'adaptive', 'interval'],
                       help='自适应模式')
    parser.add_argument('--interval', type=float, default=10.0,
                       help='时间间隔（秒），用于 interval 模式')
    parser.add_argument('--frames-per-interval', type=int, default=1,
                       help='每个时间间隔提取的帧数')
    parser.add_argument('--min-frames', type=int, default=3,
                       help='最小帧数')
    parser.add_argument('--max-frames', type=int, default=30,
                       help='最大帧数')
    parser.add_argument('--resolution', 
                       choices=['original', '1080p', '720p', '480p', '360p', '240p'],
                       default='original',
                       help='输出图像分辨率')
    parser.add_argument('--base64', action='store_true',
                       help='返回base64编码（用于AI分析）')
    parser.add_argument('--save-files', action='store_true',
                       help='保存图像文件到磁盘')
    
    args = parser.parse_args()
    
    # 验证参数
    if args.save_files and not args.output:
        parser.error("当使用 --save-files 时必须指定 -o/--output 输出目录")
    
    if not args.base64 and not args.save_files:
        logger.warning("既未指定 --base64 也未指定 --save-files，将默认启用 --base64")
        args.base64 = True
    
    # 处理参数
    try:
        k = int(args.keyframes) if args.keyframes != 'auto' else 'auto'
    except ValueError:
        k = 'auto'
    
    result = extract_top_k_keyframes(
        args.input, 
        args.output, 
        k=k,
        adaptive_mode=args.mode,
        interval=args.interval,
        frames_per_interval=args.frames_per_interval,
        min_frames=args.min_frames,
        max_frames=args.max_frames,
        resolution=args.resolution,
        return_base64=args.base64,
        save_files=args.save_files
    )
    
    if 'error' in result:
        logger.error(f"错误: {result['error']}")
        sys.exit(1)
    
    # 输出base64结果（用于Azure OpenAI分析）
    if args.base64:
        print("\n" + "="*50)
        print("Azure OpenAI 分析用 Base64 数据:")
        print("="*50)
        for i, frame in enumerate(result['frames']):
            if 'base64' in frame:
                print(f"\n帧 {i+1} (时间: {frame['timestamp']:.1f}s):")
                print(f"data:image/jpeg;base64,{frame['base64'][:100]}...")
                print(f"完整长度: {len(frame['base64'])} 字符")


if __name__ == "__main__":
    main()
