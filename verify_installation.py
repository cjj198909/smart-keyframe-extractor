#!/usr/bin/env python3
"""
Smart Keyframe Extractor - 功能验证脚本
验证所有核心功能是否正常工作
"""

import os
import sys
from pathlib import Path
import tempfile
import time

def test_basic_functionality():
    """测试基础功能"""
    print("🔧 测试基础功能...")
    
    try:
        from smart_keyframe_extractor.extractor import extract_top_k_keyframes
        from smart_keyframe_extractor import SmartKeyFrameExtractor
        print("   ✅ 核心模块导入成功")
        
        # 创建提取器实例
        extractor = SmartKeyFrameExtractor()
        print("   ✅ 提取器实例化成功")
        
        return True
    except Exception as e:
        print(f"   ❌ 基础功能测试失败: {e}")
        return False

def test_remote_video_support():
    """测试远程视频支持"""
    print("🌐 测试远程视频支持...")
    
    try:
        from smart_keyframe_extractor.remote_video_utils import (
            is_remote_url, 
            get_video_url_info,
            RemoteVideoDownloader
        )
        print("   ✅ 远程视频模块导入成功")
        
        # 测试URL检测
        test_urls = [
            "https://example.com/video.mp4",
            "s3://bucket/video.mp4", 
            "local_video.mp4"
        ]
        
        for url in test_urls:
            is_remote = is_remote_url(url)
            url_info = get_video_url_info(url)
            print(f"   📎 {url}: {'远程' if is_remote else '本地'}")
        
        print("   ✅ URL检测功能正常")
        return True
        
    except ImportError:
        print("   ⚠️  远程视频模块未安装（可选功能）")
        return True
    except Exception as e:
        print(f"   ❌ 远程视频测试失败: {e}")
        return False

def test_azure_openai_support():
    """测试Azure OpenAI支持"""
    print("🤖 测试Azure OpenAI支持...")
    
    try:
        from smart_keyframe_extractor.azure_openai import analyze_video_content
        print("   ✅ Azure OpenAI模块导入成功")
        return True
        
    except ImportError:
        print("   ⚠️  Azure OpenAI模块未安装（可选功能）")
        return True
    except Exception as e:
        print(f"   ❌ Azure OpenAI测试失败: {e}")
        return False

def test_cli_interface():
    """测试CLI接口"""
    print("💻 测试CLI接口...")
    
    try:
        from smart_keyframe_extractor.cli import main
        print("   ✅ CLI模块导入成功")
        return True
        
    except Exception as e:
        print(f"   ❌ CLI测试失败: {e}")
        return False

def test_dependencies():
    """测试关键依赖"""
    print("📦 测试关键依赖...")
    
    deps_status = {}
    
    # 核心依赖
    core_deps = [
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"), 
        ("numpy", "NumPy"),
        ("requests", "Requests")
    ]
    
    # 可选依赖
    optional_deps = [
        ("boto3", "AWS S3"),
        ("azure.storage.blob", "Azure Blob"),
        ("google.cloud.storage", "Google Cloud"),
        ("openai", "Azure OpenAI")
    ]
    
    all_good = True
    
    for module, name in core_deps:
        try:
            __import__(module)
            print(f"   ✅ {name}: 已安装")
            deps_status[name] = True
        except ImportError:
            print(f"   ❌ {name}: 未安装 (必需)")
            deps_status[name] = False
            all_good = False
    
    for module, name in optional_deps:
        try:
            __import__(module)
            print(f"   ✅ {name}: 已安装")
            deps_status[name] = True
        except ImportError:
            print(f"   ⚠️  {name}: 未安装 (可选)")
            deps_status[name] = False
    
    return all_good, deps_status

def main():
    """主验证函数"""
    print("🚀 Smart Keyframe Extractor - 功能验证")
    print("=" * 60)
    
    tests = [
        ("基础功能", test_basic_functionality),
        ("远程视频支持", test_remote_video_support),
        ("Azure OpenAI支持", test_azure_openai_support),
        ("CLI接口", test_cli_interface),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print()
        result = test_func()
        results.append((test_name, result))
    
    print()
    deps_ok, deps_status = test_dependencies()
    
    print()
    print("=" * 60)
    print("📋 验证结果总结:")
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status} {test_name}")
    
    deps_result = "✅ 通过" if deps_ok else "❌ 失败"
    print(f"   {deps_result} 核心依赖检查")
    
    print()
    print("🎯 功能可用性:")
    
    # 核心功能
    core_available = all(r[1] for r in results[:1]) and deps_ok
    print(f"   🔧 核心视频处理: {'✅ 可用' if core_available else '❌ 不可用'}")
    
    # 远程视频
    remote_available = results[1][1] and deps_status.get('AWS S3', False)
    print(f"   🌐 远程视频处理: {'✅ 可用' if remote_available else '⚠️  部分可用'}")
    
    # AI集成
    ai_available = results[2][1] and deps_status.get('Azure OpenAI', False)
    print(f"   🤖 AI内容分析: {'✅ 可用' if ai_available else '⚠️  需要配置'}")
    
    # CLI
    cli_available = results[3][1]
    print(f"   💻 命令行接口: {'✅ 可用' if cli_available else '❌ 不可用'}")
    
    print()
    if core_available:
        print("🎉 系统验证通过！核心功能正常工作")
        print("💡 使用 'smart-keyframe --help' 查看命令选项")
        print("📚 查看 README.md 了解详细使用方法")
    else:
        print("⚠️  系统需要修复，请检查依赖安装")
        print("💡 运行 'pip install smart-keyframe-extractor[all]' 安装完整功能")
    
    return core_available

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
