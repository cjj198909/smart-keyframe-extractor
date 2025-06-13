"""
远程视频处理工具模块
支持从HTTP/HTTPS URL、云存储等远程源下载和处理视频
"""

import os
import tempfile
import logging
import shutil
import time
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import hashlib

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    from azure.storage.blob import BlobServiceClient
    from azure.core.exceptions import AzureError
    HAS_AZURE_STORAGE = True
except ImportError:
    HAS_AZURE_STORAGE = False

try:
    from google.cloud import storage as gcs
    from google.api_core import exceptions as gcs_exceptions
    HAS_GCS = True
except ImportError:
    HAS_GCS = False

logger = logging.getLogger(__name__)


class RemoteVideoDownloader:
    """远程视频下载器"""
    
    def __init__(self, cache_dir: Optional[str] = None, max_cache_size_gb: float = 5.0):
        """
        初始化远程视频下载器
        
        Args:
            cache_dir: 缓存目录，如果为None则使用系统临时目录
            max_cache_size_gb: 最大缓存大小（GB）
        """
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "smart_keyframe_cache")
        self.max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024  # 转换为字节
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_path(self, url: str) -> str:
        """根据URL生成缓存文件路径"""
        # 使用URL的hash作为文件名，避免特殊字符问题
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # 尝试从URL中提取文件扩展名
        parsed_url = urlparse(url)
        path = parsed_url.path
        if '.' in path:
            ext = path.split('.')[-1].lower()
            # 验证是否为常见视频格式
            if ext in ['mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', '3gp', 'wmv']:
                return os.path.join(self.cache_dir, f"{url_hash}.{ext}")
        
        # 默认使用mp4扩展名
        return os.path.join(self.cache_dir, f"{url_hash}.mp4")
    
    def _cleanup_cache(self):
        """清理缓存，保持在大小限制内"""
        try:
            cache_files = []
            total_size = 0
            
            # 收集所有缓存文件的信息
            for file_path in Path(self.cache_dir).glob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    cache_files.append({
                        'path': file_path,
                        'size': stat.st_size,
                        'mtime': stat.st_mtime
                    })
                    total_size += stat.st_size
            
            # 如果超过限制，删除最旧的文件
            if total_size > self.max_cache_size:
                # 按修改时间排序（最旧的在前）
                cache_files.sort(key=lambda x: x['mtime'])
                
                for file_info in cache_files:
                    if total_size <= self.max_cache_size * 0.8:  # 清理到80%
                        break
                    
                    try:
                        file_info['path'].unlink()
                        total_size -= file_info['size']
                        logger.info(f"已清理缓存文件: {file_info['path']}")
                    except OSError as e:
                        logger.warning(f"清理缓存文件失败 {file_info['path']}: {e}")
                        
        except Exception as e:
            logger.warning(f"缓存清理失败: {e}")
    
    def _download_http_video(self, url: str, output_path: str) -> bool:
        """
        从HTTP/HTTPS URL下载视频
        
        Args:
            url: 视频URL
            output_path: 输出文件路径
            
        Returns:
            是否下载成功
        """
        if not HAS_REQUESTS:
            raise ImportError("需要安装 requests 库来支持HTTP下载: pip install requests")
        
        try:
            logger.info(f"开始下载视频: {url}")
            
            # 发送HEAD请求获取文件大小
            head_response = requests.head(url, timeout=30)
            if head_response.status_code != 200:
                logger.error(f"无法访问URL: {url}, 状态码: {head_response.status_code}")
                return False
            
            content_length = head_response.headers.get('content-length')
            if content_length:
                file_size = int(content_length)
                logger.info(f"文件大小: {file_size / 1024 / 1024:.1f} MB")
            
            # 下载文件
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 每10MB显示一次进度
                        if downloaded % (10 * 1024 * 1024) == 0:
                            if content_length:
                                progress = (downloaded / file_size) * 100
                                logger.info(f"下载进度: {progress:.1f}%")
            
            logger.info(f"视频下载完成: {output_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP下载失败: {e}")
            return False
        except Exception as e:
            logger.error(f"下载过程中出错: {e}")
            return False
    
    def _download_s3_video(self, url: str, output_path: str) -> bool:
        """
        从AWS S3下载视频
        
        Args:
            url: S3 URL (s3://bucket/key 或 https://bucket.s3.region.amazonaws.com/key)
            output_path: 输出文件路径
            
        Returns:
            是否下载成功
        """
        if not HAS_BOTO3:
            raise ImportError("需要安装 boto3 库来支持S3下载: pip install boto3")
        
        try:
            # 解析S3 URL
            if url.startswith('s3://'):
                # s3://bucket/key 格式
                parts = url[5:].split('/', 1)
                bucket = parts[0]
                key = parts[1] if len(parts) > 1 else ''
            else:
                # https://bucket.s3.region.amazonaws.com/key 格式
                parsed = urlparse(url)
                path_parts = parsed.path.lstrip('/').split('/', 1)
                if 's3.' in parsed.netloc:
                    bucket = parsed.netloc.split('.')[0]
                    key = parsed.path.lstrip('/')
                else:
                    bucket = path_parts[0]
                    key = path_parts[1] if len(path_parts) > 1 else ''
            
            logger.info(f"从S3下载: bucket={bucket}, key={key}")
            
            # 创建S3客户端
            s3_client = boto3.client('s3')
            
            # 下载文件
            s3_client.download_file(bucket, key, output_path)
            logger.info(f"S3视频下载完成: {output_path}")
            return True
            
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"S3下载失败: {e}")
            return False
        except Exception as e:
            logger.error(f"S3下载过程中出错: {e}")
            return False
    
    def _download_azure_video(self, url: str, output_path: str) -> bool:
        """
        从Azure Blob Storage下载视频
        
        Args:
            url: Azure URL
            output_path: 输出文件路径
            
        Returns:
            是否下载成功
        """
        if not HAS_AZURE_STORAGE:
            raise ImportError("需要安装 azure-storage-blob 库: pip install azure-storage-blob")
        
        try:
            # 解析Azure URL
            parsed = urlparse(url)
            
            if 'blob.core.windows.net' not in parsed.netloc:
                logger.error(f"不是有效的Azure Blob URL: {url}")
                return False
            
            # 提取账户名、容器名和blob名
            account_name = parsed.netloc.split('.')[0]
            path_parts = parsed.path.lstrip('/').split('/', 1)
            container_name = path_parts[0]
            blob_name = path_parts[1] if len(path_parts) > 1 else ''
            
            logger.info(f"从Azure下载: account={account_name}, container={container_name}, blob={blob_name}")
            
            # 创建blob客户端（使用匿名访问或SAS token）
            blob_service_client = BlobServiceClient(account_url=f"https://{account_name}.blob.core.windows.net")
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            
            # 下载文件
            with open(output_path, 'wb') as f:
                download_stream = blob_client.download_blob()
                f.write(download_stream.readall())
            
            logger.info(f"Azure视频下载完成: {output_path}")
            return True
            
        except AzureError as e:
            logger.error(f"Azure下载失败: {e}")
            return False
        except Exception as e:
            logger.error(f"Azure下载过程中出错: {e}")
            return False
    
    def _download_gcs_video(self, url: str, output_path: str) -> bool:
        """
        从Google Cloud Storage下载视频
        
        Args:
            url: GCS URL
            output_path: 输出文件路径
            
        Returns:
            是否下载成功
        """
        if not HAS_GCS:
            raise ImportError("需要安装 google-cloud-storage 库: pip install google-cloud-storage")
        
        try:
            # 解析GCS URL
            if url.startswith('gs://'):
                # gs://bucket/object 格式
                parts = url[5:].split('/', 1)
                bucket_name = parts[0]
                object_name = parts[1] if len(parts) > 1 else ''
            else:
                # https://storage.googleapis.com/bucket/object 格式
                parsed = urlparse(url)
                if 'storage.googleapis.com' in parsed.netloc:
                    path_parts = parsed.path.lstrip('/').split('/', 1)
                    bucket_name = path_parts[0]
                    object_name = path_parts[1] if len(path_parts) > 1 else ''
                else:
                    logger.error(f"不是有效的GCS URL: {url}")
                    return False
            
            logger.info(f"从GCS下载: bucket={bucket_name}, object={object_name}")
            
            # 创建GCS客户端
            client = gcs.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            
            # 下载文件
            blob.download_to_filename(output_path)
            logger.info(f"GCS视频下载完成: {output_path}")
            return True
            
        except gcs_exceptions.GoogleCloudError as e:
            logger.error(f"GCS下载失败: {e}")
            return False
        except Exception as e:
            logger.error(f"GCS下载过程中出错: {e}")
            return False
    
    def download_video(self, url: str, use_cache: bool = True) -> Optional[str]:
        """
        下载远程视频到本地临时文件
        
        Args:
            url: 视频URL
            use_cache: 是否使用缓存
            
        Returns:
            本地文件路径，如果下载失败则返回None
        """
        if use_cache:
            cache_path = self._get_cache_path(url)
            if os.path.exists(cache_path):
                logger.info(f"使用缓存文件: {cache_path}")
                # 更新访问时间
                os.utime(cache_path, None)
                return cache_path
        
        # 确定输出路径
        if use_cache:
            output_path = cache_path
        else:
            # 创建临时文件
            parsed_url = urlparse(url)
            ext = 'mp4'
            if '.' in parsed_url.path:
                potential_ext = parsed_url.path.split('.')[-1].lower()
                if potential_ext in ['mp4', 'mov', 'avi', 'mkv', 'webm', 'flv']:
                    ext = potential_ext
            
            fd, output_path = tempfile.mkstemp(suffix=f'.{ext}', prefix='video_')
            os.close(fd)
        
        # 根据URL类型选择下载方法
        success = False
        url_lower = url.lower()
        
        try:
            if url_lower.startswith(('http://', 'https://')):
                if 's3.' in url_lower and 'amazonaws.com' in url_lower:
                    success = self._download_s3_video(url, output_path)
                elif 'blob.core.windows.net' in url_lower:
                    success = self._download_azure_video(url, output_path)
                elif 'storage.googleapis.com' in url_lower:
                    success = self._download_gcs_video(url, output_path)
                else:
                    success = self._download_http_video(url, output_path)
            elif url_lower.startswith('s3://'):
                success = self._download_s3_video(url, output_path)
            elif url_lower.startswith('gs://'):
                success = self._download_gcs_video(url, output_path)
            else:
                logger.error(f"不支持的URL格式: {url}")
                return None
            
            if success:
                if use_cache:
                    self._cleanup_cache()
                return output_path
            else:
                # 下载失败，清理文件
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return None
                
        except Exception as e:
            logger.error(f"下载视频失败: {e}")
            if os.path.exists(output_path):
                os.unlink(output_path)
            return None
    
    def cleanup_temp_file(self, file_path: str):
        """
        清理临时文件（仅清理非缓存文件）
        
        Args:
            file_path: 文件路径
        """
        try:
            # 只清理不在缓存目录中的文件
            if not file_path.startswith(self.cache_dir):
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.debug(f"已清理临时文件: {file_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败 {file_path}: {e}")


def is_remote_url(path: str) -> bool:
    """
    检查是否为远程URL
    
    Args:
        path: 文件路径或URL
        
    Returns:
        是否为远程URL
    """
    if not isinstance(path, str):
        return False
    
    path_lower = path.lower()
    return (
        path_lower.startswith(('http://', 'https://')) or
        path_lower.startswith('s3://') or
        path_lower.startswith('gs://') or
        'blob.core.windows.net' in path_lower or
        'storage.googleapis.com' in path_lower
    )


def get_video_url_info(url: str) -> Dict[str, Any]:
    """
    获取远程视频URL的基本信息
    
    Args:
        url: 视频URL
        
    Returns:
        包含URL信息的字典
    """
    parsed = urlparse(url)
    
    info = {
        'url': url,
        'scheme': parsed.scheme,
        'hostname': parsed.hostname,
        'path': parsed.path,
        'is_remote': is_remote_url(url)
    }
    
    # 尝试确定视频格式
    if '.' in parsed.path:
        ext = parsed.path.split('.')[-1].lower()
        if ext in ['mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', '3gp', 'wmv']:
            info['format'] = ext
    
    # 确定存储类型
    hostname_lower = (parsed.hostname or '').lower()
    if 's3.' in hostname_lower and 'amazonaws.com' in hostname_lower:
        info['storage_type'] = 'aws_s3'
    elif 'blob.core.windows.net' in hostname_lower:
        info['storage_type'] = 'azure_blob'
    elif 'storage.googleapis.com' in hostname_lower:
        info['storage_type'] = 'google_cloud'
    elif parsed.scheme.startswith('http'):
        info['storage_type'] = 'http'
    elif parsed.scheme == 's3':
        info['storage_type'] = 'aws_s3'
    elif parsed.scheme == 'gs':
        info['storage_type'] = 'google_cloud'
    else:
        info['storage_type'] = 'unknown'
    
    return info
