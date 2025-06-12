#!/usr/bin/env python3
"""
快速测试脚本 - 演示 smart-keyframe-extractor 功能
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

def create_test_video():
    """创建一个测试视频"""
    print("🎬 创建测试视频...")
    
    # 使用FFmpeg创建一个简单的测试视频
    output_path = "test_video.mp4"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=10:size=640x480:rate=30",
        "-f", "lavfi", 
        "-i", "sine=frequency=1000:duration=10",
        "-shortest",
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"✅ 测试视频创建成功: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"❌ 创建测试视频失败: {e}")
        return None
    except FileNotFoundError:
        print("❌ 未找到FFmpeg，请先安装FFmpeg")
        return None

def test_basic_extraction():
    """测试基础关键帧提取"""
    print("\n🧪 测试基础关键帧提取...")
    
    video_path = create_test_video()
    if not video_path:
        return False
    
    try:
        from smart_keyframe_extractor import extract_top_k_keyframes
        
        result = extract_top_k_keyframes(
            video_path=video_path,
            k=3,
            resolution="480p",
            return_base64=True,
            save_files=False
        )
        
        if 'error' in result:
            print(f"❌ 提取失败: {result['error']}")
            return False
        
        print(f"✅ 成功提取 {result['extracted_frames']} 帧")
        print(f"   视频时长: {result['video_duration']:.1f}秒")
        print(f"   分辨率: {result['resolution']}")
        
        for i, frame in enumerate(result['frames']):
            print(f"   帧 {i+1}: 时间 {frame['timestamp']:.1f}s, base64长度 {len(frame.get('base64', ''))}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists(video_path):
            os.remove(video_path)

def test_command_line():
    """测试命令行工具"""
    print("\n🖥️  测试命令行工具...")
    
    video_path = create_test_video()
    if not video_path:
        return False
    
    try:
        cmd = [
            "smart-keyframe", video_path,
            "-k", "3",
            "--resolution", "360p",
            "--base64"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 命令行工具运行成功")
            if "Azure OpenAI 分析用 Base64 数据" in result.stdout:
                print("✅ Base64输出正常")
            return True
        else:
            print(f"❌ 命令行工具失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 命令行测试失败: {e}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists(video_path):
            os.remove(video_path)

def test_vision_utils():
    """测试视觉工具"""
    print("\n🔧 测试视觉工具...")
    
    try:
        from smart_keyframe_extractor.vision_utils import smart_resize, image_to_base64
        from PIL import Image
        
        # 测试智能调整大小
        h, w = smart_resize(1920, 1080)
        print(f"✅ 智能调整大小: 1920x1080 -> {w}x{h}")
        
        # 测试base64转换
        test_image = Image.new('RGB', (100, 100), color='red')
        base64_str = image_to_base64(test_image)
        print(f"✅ Base64转换: 生成{len(base64_str)}字符")
        
        return True
        
    except Exception as e:
        print(f"❌ 视觉工具测试失败: {e}")
        return False

def test_azure_import():
    """测试Azure OpenAI导入"""
    print("\n☁️  测试Azure OpenAI集成...")
    
    try:
        from smart_keyframe_extractor.azure_openai import AzureOpenAIAnalyzer
        print("✅ Azure OpenAI模块导入成功")
        
        # 测试分析器初始化（不提供真实凭据）
        try:
            analyzer = AzureOpenAIAnalyzer(api_key="test", endpoint="https://test.com")
            print("✅ 分析器初始化成功")
        except Exception as e:
            if "需要提供" in str(e):
                print("✅ 凭据验证正常")
            else:
                raise
        
        return True
        
    except ImportError:
        print("⚠️  Azure OpenAI集成不可用（需要安装openai包）")
        return True  # 这不算失败，因为是可选依赖
    except Exception as e:
        print(f"❌ Azure OpenAI测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 Smart Keyframe Extractor 测试套件")
    print("=" * 50)
    
    tests = [
        ("基础功能测试", test_basic_extraction),
        ("命令行工具测试", test_command_line),
        ("视觉工具测试", test_vision_utils),
        ("Azure集成测试", test_azure_import)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} 通过")
        else:
            print(f"❌ {test_name} 失败")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
