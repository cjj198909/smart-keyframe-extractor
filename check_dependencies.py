#!/usr/bin/env python3
"""
依赖检查脚本
验证Smart Keyframe Extractor的所有依赖是否正确安装
"""

import sys
import importlib
from typing import Dict, List, Tuple

def check_dependency(module_name: str, description: str) -> Tuple[bool, str]:
    """检查单个依赖"""
    try:
        importlib.import_module(module_name)
        return True, f"✅ {description}"
    except ImportError as e:
        return False, f"❌ {description} - 缺失: {str(e)}"

def check_dependencies() -> None:
    """检查所有依赖"""
    print("🔍 检查 Smart Keyframe Extractor 依赖...")
    print("=" * 60)
    
    # 核心依赖
    core_deps = [
        ("cv2", "OpenCV (opencv-python) - 视频处理核心"),
        ("PIL", "Pillow - 图像处理"),
        ("numpy", "NumPy - 数值计算"),
        ("requests", "Requests - HTTP请求"),
    ]
    
    # 远程视频依赖
    remote_deps = [
        ("boto3", "AWS S3支持 - boto3"),
        ("botocore", "AWS核心库 - botocore"),
        ("azure.storage.blob", "Azure Blob Storage - azure-storage-blob"),
        ("azure.core", "Azure核心库 - azure-core"),
        ("google.cloud.storage", "Google Cloud Storage - google-cloud-storage"),
        ("google.api_core", "Google API核心 - google-api-core"),
    ]
    
    # Azure OpenAI依赖
    azure_deps = [
        ("openai", "Azure OpenAI - openai"),
    ]
    
    # 检查核心依赖
    print("📦 核心依赖:")
    core_results = []
    for module, desc in core_deps:
        success, message = check_dependency(module, desc)
        core_results.append(success)
        print(f"   {message}")
    
    print()
    
    # 检查远程视频依赖
    print("🌐 远程视频支持依赖:")
    remote_results = []
    for module, desc in remote_deps:
        success, message = check_dependency(module, desc)
        remote_results.append(success)
        print(f"   {message}")
    
    print()
    
    # 检查Azure OpenAI依赖
    print("🤖 Azure OpenAI支持依赖:")
    azure_results = []
    for module, desc in azure_deps:
        success, message = check_dependency(module, desc)
        azure_results.append(success)
        print(f"   {message}")
    
    print()
    print("=" * 60)
    
    # 总结
    core_ok = all(core_results)
    remote_ok = all(remote_results)
    azure_ok = all(azure_results)
    
    print("📋 依赖状态总结:")
    print(f"   🔧 核心功能: {'✅ 可用' if core_ok else '❌ 缺少依赖'}")
    print(f"   🌐 远程视频: {'✅ 可用' if remote_ok else '❌ 缺少依赖'}")
    print(f"   🤖 Azure OpenAI: {'✅ 可用' if azure_ok else '❌ 缺少依赖'}")
    
    print()
    
    # 安装建议
    if not core_ok:
        print("🚨 核心依赖缺失，请运行:")
        print("   pip install smart-keyframe-extractor")
    
    if not remote_ok:
        print("💡 远程视频支持未安装，如需处理云存储视频请运行:")
        print("   pip install smart-keyframe-extractor[remote]")
        print("   或: pip install smart-keyframe-extractor[all]")
    
    if not azure_ok:
        print("💡 Azure OpenAI支持未安装，如需AI分析功能请运行:")
        print("   pip install smart-keyframe-extractor[azure]")
        print("   或: pip install smart-keyframe-extractor[all]")
    
    if core_ok and remote_ok and azure_ok:
        print("🎉 所有依赖都已正确安装！")
        print("   您可以使用完整的功能集合")
    
    print()
    print("📚 更多安装选项:")
    print("   - 完整安装: pip install smart-keyframe-extractor[all]")
    print("   - 基础功能: pip install smart-keyframe-extractor")
    print("   - 远程视频: pip install smart-keyframe-extractor[remote]")
    print("   - Azure OpenAI: pip install smart-keyframe-extractor[azure]")

if __name__ == "__main__":
    check_dependencies()
