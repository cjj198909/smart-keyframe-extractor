#!/usr/bin/env python3
"""
远程视频功能测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_keyframe_extractor import (
    extract_top_k_keyframes, 
    is_remote_url, 
    get_video_url_info,
    RemoteVideoDownloader
)

def test_url_detection():
    """测试URL检测功能"""
    print("=== URL检测测试 ===")
    
    test_urls = [
        "video.mp4",  # 本地文件
        "https://example.com/video.mp4",  # HTTP
        "http://example.com/video.mp4",   # HTTP
        "s3://bucket/video.mp4",          # S3
        "gs://bucket/video.mp4",          # GCS
        "https://account.blob.core.windows.net/container/video.mp4",  # Azure
        "/path/to/video.mp4",             # 绝对路径
        "ftp://example.com/video.mp4",    # 不支持的协议
    ]
    
    for url in test_urls:
        is_remote = is_remote_url(url)
        print(f"  {url:60} -> {'远程' if is_remote else '本地'}")
        
        if is_remote:
            url_info = get_video_url_info(url)
            print(f"    类型: {url_info['storage_type']}, "
                  f"协议: {url_info['scheme']}, "
                  f"域名: {url_info.get('hostname', 'N/A')}")

def test_remote_downloader():
    """测试远程下载器"""
    print("\n=== 远程下载器测试 ===")
    
    try:
        downloader = RemoteVideoDownloader()
        print(f"✅ 下载器初始化成功")
        print(f"   缓存目录: {downloader.cache_dir}")
        print(f"   缓存限制: {downloader.max_cache_size / (1024**3):.1f}GB")
        
    except Exception as e:
        print(f"❌ 下载器初始化失败: {e}")

def test_extractor_with_remote():
    """测试提取器的远程支持"""
    print("\n=== 提取器远程支持测试 ===")
    
    try:
        from smart_keyframe_extractor.extractor import SmartKeyFrameExtractor
        
        # 测试启用远程支持
        extractor = SmartKeyFrameExtractor(enable_remote=True)
        print(f"✅ 提取器（远程支持）初始化成功")
        print(f"   远程支持: {extractor.enable_remote}")
        print(f"   下载器: {'可用' if extractor.remote_downloader else '不可用'}")
        
        # 测试禁用远程支持
        extractor_no_remote = SmartKeyFrameExtractor(enable_remote=False)
        print(f"✅ 提取器（无远程支持）初始化成功")
        print(f"   远程支持: {extractor_no_remote.enable_remote}")
        print(f"   下载器: {'可用' if extractor_no_remote.remote_downloader else '不可用'}")
        
    except Exception as e:
        print(f"❌ 提取器测试失败: {e}")

def test_with_sample_url():
    """使用示例URL测试（不实际下载）"""
    print("\n=== 示例URL测试 ===")
    
    # 使用一个常用的测试视频URL
    test_url = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
    
    print(f"测试URL: {test_url}")
    print(f"是否为远程: {is_remote_url(test_url)}")
    
    url_info = get_video_url_info(test_url)
    print(f"URL信息: {url_info}")
    
    print("\n注意: 实际下载和处理需要网络连接和有效的视频URL")

def main():
    """主测试函数"""
    print("Smart Keyframe Extractor - 远程视频功能测试")
    print("=" * 60)
    
    # 检查远程视频模块是否可用
    try:
        from smart_keyframe_extractor.remote_video_utils import HAS_REQUESTS, HAS_BOTO3, HAS_AZURE_STORAGE, HAS_GCS
        print("📦 依赖检查:")
        print(f"  requests: {'✅' if HAS_REQUESTS else '❌'}")
        print(f"  boto3: {'✅' if HAS_BOTO3 else '❌'}")
        print(f"  azure-storage-blob: {'✅' if HAS_AZURE_STORAGE else '❌'}")
        print(f"  google-cloud-storage: {'✅' if HAS_GCS else '❌'}")
        
        if not any([HAS_REQUESTS, HAS_BOTO3, HAS_AZURE_STORAGE, HAS_GCS]):
            print("\n❌ 没有安装任何远程视频依赖")
            print("请运行: pip install requests boto3 azure-storage-blob google-cloud-storage")
            return
        
    except ImportError:
        print("❌ 无法导入远程视频模块")
        return
    
    # 运行测试
    test_url_detection()
    test_remote_downloader()
    test_extractor_with_remote()
    test_with_sample_url()
    
    print("\n" + "=" * 60)
    print("✅ 远程视频功能测试完成!")
    print("\n下一步:")
    print("1. 配置云服务凭证（如需要）")
    print("2. 运行 python scripts/setup_remote_video.py 检查配置")
    print("3. 尝试处理实际的远程视频")

if __name__ == "__main__":
    main()
