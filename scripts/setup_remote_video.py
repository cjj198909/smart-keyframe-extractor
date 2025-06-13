#!/usr/bin/env python3
"""
远程视频支持配置检查脚本
检查远程视频处理所需的依赖和配置
"""

import os
import sys
import subprocess

def check_dependency(package_name, import_name=None):
    """检查Python包依赖"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True, "已安装"
    except ImportError:
        return False, "未安装"

def check_aws_credentials():
    """检查AWS凭证配置"""
    credentials = []
    
    # 检查环境变量
    if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
        credentials.append("环境变量")
    
    # 检查AWS CLI配置文件
    aws_config_path = os.path.expanduser('~/.aws/credentials')
    if os.path.exists(aws_config_path):
        credentials.append("AWS CLI配置文件")
    
    # 检查AWS CLI是否安装
    try:
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            credentials.append("AWS CLI可用")
    except FileNotFoundError:
        pass
    
    return credentials

def check_azure_credentials():
    """检查Azure凭证配置"""
    credentials = []
    
    # 检查环境变量
    if os.getenv('AZURE_STORAGE_CONNECTION_STRING'):
        credentials.append("连接字符串（环境变量）")
    
    if os.getenv('AZURE_STORAGE_ACCOUNT_NAME') and os.getenv('AZURE_STORAGE_ACCOUNT_KEY'):
        credentials.append("账户名+密钥（环境变量）")
    
    return credentials

def check_gcp_credentials():
    """检查Google Cloud凭证配置"""
    credentials = []
    
    # 检查环境变量
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        credentials.append("服务账户密钥文件")
    
    # 检查gcloud CLI
    try:
        result = subprocess.run(['gcloud', 'auth', 'list', '--format=value(account)'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            credentials.append("gcloud CLI认证")
    except FileNotFoundError:
        pass
    
    return credentials

def main():
    """主检查函数"""
    print("Smart Keyframe Extractor - 远程视频支持检查")
    print("=" * 60)
    
    # 1. 检查基础依赖
    print("\n📦 基础依赖检查:")
    dependencies = [
        ('requests', 'requests'),
        ('boto3', 'boto3'),
        ('azure-storage-blob', 'azure.storage.blob'),
        ('google-cloud-storage', 'google.cloud.storage')
    ]
    
    missing_deps = []
    for package, import_name in dependencies:
        available, status = check_dependency(package, import_name)
        status_icon = "✅" if available else "❌"
        print(f"  {status_icon} {package}: {status}")
        if not available:
            missing_deps.append(package)
    
    # 2. 安装建议
    if missing_deps:
        print(f"\n🔧 安装缺失依赖:")
        print(f"pip install {' '.join(missing_deps)}")
        print("\n或安装所有依赖:")
        print("pip install requests boto3 azure-storage-blob google-cloud-storage")
    
    # 3. 检查云服务凭证
    print("\n🔐 云服务凭证检查:")
    
    # AWS
    aws_creds = check_aws_credentials()
    if aws_creds:
        print(f"  ✅ AWS S3: {', '.join(aws_creds)}")
    else:
        print("  ❌ AWS S3: 未配置凭证")
        print("     配置方法:")
        print("     - 运行: aws configure")
        print("     - 或设置环境变量: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
    
    # Azure
    azure_creds = check_azure_credentials()
    if azure_creds:
        print(f"  ✅ Azure Blob: {', '.join(azure_creds)}")
    else:
        print("  ❌ Azure Blob: 未配置凭证")
        print("     配置方法:")
        print("     - 设置环境变量: AZURE_STORAGE_CONNECTION_STRING")
        print("     - 或设置: AZURE_STORAGE_ACCOUNT_NAME, AZURE_STORAGE_ACCOUNT_KEY")
    
    # Google Cloud
    gcp_creds = check_gcp_credentials()
    if gcp_creds:
        print(f"  ✅ Google Cloud Storage: {', '.join(gcp_creds)}")
    else:
        print("  ❌ Google Cloud Storage: 未配置凭证")
        print("     配置方法:")
        print("     - 运行: gcloud auth login")
        print("     - 或设置环境变量: GOOGLE_APPLICATION_CREDENTIALS")
    
    # 4. 缓存配置
    print("\n💾 缓存配置:")
    cache_dir = os.getenv('REMOTE_VIDEO_CACHE_DIR')
    if cache_dir:
        print(f"  ✅ 自定义缓存目录: {cache_dir}")
        if not os.path.exists(cache_dir):
            print(f"     ⚠️  目录不存在，将自动创建")
    else:
        print("  ℹ️  使用默认缓存目录（系统临时目录）")
        print("     可设置环境变量: REMOTE_VIDEO_CACHE_DIR")
    
    # 5. 使用示例
    print("\n📋 使用示例:")
    print("  # HTTP/HTTPS URL")
    print("  smart-keyframe https://example.com/video.mp4 -k 5 --base64")
    print("")
    print("  # AWS S3")
    print("  smart-keyframe s3://bucket/video.mp4 -k auto --resolution 720p --base64")
    print("")
    print("  # Azure Blob Storage")
    print("  smart-keyframe https://account.blob.core.windows.net/container/video.mp4 -k 5 --base64")
    print("")
    print("  # Google Cloud Storage")
    print("  smart-keyframe gs://bucket/video.mp4 -k auto --resolution 480p --base64")
    
    # 6. 环境变量配置模板
    print("\n🔧 环境变量配置模板:")
    print("# AWS")
    print("export AWS_ACCESS_KEY_ID='your-access-key'")
    print("export AWS_SECRET_ACCESS_KEY='your-secret-key'")
    print("export AWS_DEFAULT_REGION='us-east-1'")
    print("")
    print("# Azure")
    print("export AZURE_STORAGE_CONNECTION_STRING='DefaultEndpointsProtocol=https;...'")
    print("# 或")
    print("export AZURE_STORAGE_ACCOUNT_NAME='your-account'")
    print("export AZURE_STORAGE_ACCOUNT_KEY='your-key'")
    print("")
    print("# Google Cloud")
    print("export GOOGLE_APPLICATION_CREDENTIALS='/path/to/service-account-key.json'")
    print("")
    print("# 缓存配置")
    print("export REMOTE_VIDEO_CACHE_DIR='/path/to/cache/directory'")
    
    print("\n" + "=" * 60)
    
    # 总结
    if not missing_deps and (aws_creds or azure_creds or gcp_creds):
        print("✅ 远程视频支持已准备就绪!")
    elif not missing_deps:
        print("⚠️  依赖已安装，但需要配置云服务凭证")
    else:
        print("❌ 需要安装依赖包才能使用远程视频功能")

if __name__ == "__main__":
    main()
