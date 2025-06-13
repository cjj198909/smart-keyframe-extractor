#!/usr/bin/env python3
"""
远程视频处理示例
演示如何处理HTTP/HTTPS URL、云存储中的视频文件
"""

import os
import sys
from smart_keyframe_extractor import extract_top_k_keyframes, is_remote_url, get_video_url_info
from smart_keyframe_extractor.azure_openai import analyze_video_with_azure_openai

def example_http_video():
    """处理HTTP/HTTPS视频示例"""
    print("=== HTTP/HTTPS 视频处理示例 ===")
    
    # 示例视频URL（请替换为实际可用的URL）
    video_url = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
    
    print(f"视频URL: {video_url}")
    print(f"是否为远程URL: {is_remote_url(video_url)}")
    
    # 获取URL信息
    url_info = get_video_url_info(video_url)
    print(f"URL信息: {url_info}")
    
    try:
        # 提取关键帧
        result = extract_top_k_keyframes(
            video_path=video_url,
            k=5,
            resolution="720p",
            return_base64=True,
            save_files=False
        )
        
        if 'error' not in result:
            print(f"✅ 成功提取 {result['extracted_frames']} 帧")
            print(f"视频时长: {result['video_duration']:.1f}秒")
            print(f"原始分辨率: {result['original_resolution']}")
            
            # 显示关键帧信息
            for i, frame in enumerate(result['frames']):
                print(f"  帧 {i+1}: 时间 {frame['timestamp']:.1f}s, "
                      f"Base64长度 {len(frame['base64'])}")
        else:
            print(f"❌ 提取失败: {result['error']}")
            
    except Exception as e:
        print(f"❌ 处理出错: {e}")

def example_s3_video():
    """处理AWS S3视频示例"""
    print("\n=== AWS S3 视频处理示例 ===")
    
    # 示例S3 URL（需要配置AWS凭证）
    s3_url = "s3://my-video-bucket/sample-video.mp4"
    
    print(f"S3 URL: {s3_url}")
    print(f"是否为远程URL: {is_remote_url(s3_url)}")
    
    # 获取URL信息
    url_info = get_video_url_info(s3_url)
    print(f"URL信息: {url_info}")
    
    # 注意：需要配置AWS凭证（AWS CLI、环境变量或IAM角色）
    print("注意: 需要配置AWS凭证才能访问S3")
    print("配置方法:")
    print("  1. 使用 aws configure 配置凭证")
    print("  2. 设置环境变量 AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY")
    print("  3. 使用IAM角色（在EC2实例上）")

def example_azure_blob_video():
    """处理Azure Blob Storage视频示例"""
    print("\n=== Azure Blob Storage 视频处理示例 ===")
    
    # 示例Azure Blob URL
    blob_url = "https://myaccount.blob.core.windows.net/videos/sample-video.mp4"
    
    print(f"Blob URL: {blob_url}")
    print(f"是否为远程URL: {is_remote_url(blob_url)}")
    
    # 获取URL信息
    url_info = get_video_url_info(blob_url)
    print(f"URL信息: {url_info}")
    
    print("注意: 需要配置Azure存储凭证")
    print("配置方法:")
    print("  1. 设置环境变量 AZURE_STORAGE_CONNECTION_STRING")
    print("  2. 或设置 AZURE_STORAGE_ACCOUNT_NAME 和 AZURE_STORAGE_ACCOUNT_KEY")

def example_gcs_video():
    """处理Google Cloud Storage视频示例"""
    print("\n=== Google Cloud Storage 视频处理示例 ===")
    
    # 示例GCS URL
    gcs_url = "gs://my-video-bucket/sample-video.mp4"
    
    print(f"GCS URL: {gcs_url}")
    print(f"是否为远程URL: {is_remote_url(gcs_url)}")
    
    # 获取URL信息
    url_info = get_video_url_info(gcs_url)
    print(f"URL信息: {url_info}")
    
    print("注意: 需要配置Google Cloud凭证")
    print("配置方法:")
    print("  1. 安装 gcloud CLI 并运行 gcloud auth login")
    print("  2. 设置环境变量 GOOGLE_APPLICATION_CREDENTIALS")
    print("  3. 使用服务账户密钥文件")

def example_with_azure_openai():
    """结合Azure OpenAI分析远程视频"""
    print("\n=== 远程视频 + Azure OpenAI 分析示例 ===")
    
    # 获取Azure OpenAI配置
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    
    if not api_key or not endpoint:
        print("❌ 需要设置Azure OpenAI环境变量:")
        print("  export AZURE_OPENAI_API_KEY='your-api-key'")
        print("  export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        return
    
    # 示例视频URL
    video_url = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
    
    try:
        # 完整的视频分析流程
        result = analyze_video_with_azure_openai(
            video_path=video_url,
            api_key=api_key,
            endpoint=endpoint,
            k=3,
            resolution="720p",
            custom_prompt="分析这个视频的主要内容和场景变化",
            detail="high"
        )
        
        if result['success']:
            print("✅ 视频分析完成!")
            print(f"提取帧数: {result['keyframe_extraction']['extracted_frames']}")
            print(f"AI分析结果: {result['video_analysis']['analysis'][:200]}...")
        else:
            print(f"❌ 分析失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 分析出错: {e}")

def main():
    """主函数"""
    print("Smart Keyframe Extractor - 远程视频处理示例")
    print("=" * 50)
    
    # 检查远程视频支持
    try:
        from smart_keyframe_extractor.remote_video_utils import RemoteVideoDownloader
        print("✅ 远程视频支持已启用")
    except ImportError:
        print("❌ 远程视频支持未启用，请安装依赖:")
        print("pip install requests boto3 azure-storage-blob google-cloud-storage")
        return
    
    # 运行示例
    example_http_video()
    example_s3_video()
    example_azure_blob_video() 
    example_gcs_video()
    example_with_azure_openai()
    
    print("\n" + "=" * 50)
    print("示例完成!")
    print("\n提示:")
    print("1. HTTP/HTTPS URL 可以直接使用")
    print("2. 云存储URL需要配置相应的访问凭证")
    print("3. 大文件会被缓存到本地以提高后续访问速度")
    print("4. 可以通过环境变量配置缓存目录: REMOTE_VIDEO_CACHE_DIR")

if __name__ == "__main__":
    main()
