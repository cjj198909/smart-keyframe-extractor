#!/usr/bin/env python3
"""
Azure OpenAI detail 参数使用示例
展示如何使用新增的 detail 参数来控制图像分析的精度和token消耗
"""

import os
import sys
from pathlib import Path

# 添加包路径
sys.path.insert(0, str(Path(__file__).parent))

from smart_keyframe_extractor import extract_top_k_keyframes
from smart_keyframe_extractor.azure_openai import AzureOpenAIAnalyzer, analyze_video_with_azure_openai

def example_basic_usage():
    """基础使用示例"""
    print("🔍 示例1: 基础 detail 参数使用")
    print("-" * 40)
    
    # 创建分析器
    analyzer = AzureOpenAIAnalyzer()
    
    # 假设已有关键帧数据
    frames = [{"base64": "dummy_base64", "timestamp": 0.0}]
    
    # 不同detail模式的使用
    examples = {
        "high": "高精度分析，适合详细内容识别",
        "low": "快速分析，适合批量处理",
        "auto": "自动选择，平衡精度和速度"
    }
    
    print("不同 detail 参数的使用场景:")
    for detail, description in examples.items():
        print(f"  • detail='{detail}': {description}")
    
    print()

def example_comparison():
    """对比不同detail参数的效果"""
    print("🔍 示例2: detail 参数效果对比")
    print("-" * 40)
    
    # 提取关键帧用于对比
    video_path = "videos/785023.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ 示例视频不存在: {video_path}")
        return
    
    print("📹 提取关键帧用于对比...")
    result = extract_top_k_keyframes(
        video_path=video_path,
        k=1,
        resolution="480p",
        return_base64=True,
        save_files=False
    )
    
    if 'error' in result:
        print(f"❌ 关键帧提取失败: {result['error']}")
        return
    
    frames = result['frames']
    print(f"✅ 成功提取 {len(frames)} 帧")
    
    # 检查Azure OpenAI配置
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        print("⚠️  Azure OpenAI 未配置，跳过实际API调用")
        print("💡 请设置环境变量 AZURE_OPENAI_API_KEY 来运行完整测试")
        return
    
    analyzer = AzureOpenAIAnalyzer()
    
    # 对比不同detail参数
    detail_modes = ["low", "high", "auto"]
    results = {}
    
    for detail in detail_modes:
        print(f"\n🔍 测试 detail='{detail}'...")
        
        analysis = analyzer.analyze_video_frames(
            frames=frames,
            custom_prompt=f"请描述这个图像的内容（使用{detail}模式分析）。",
            max_tokens=100,
            detail=detail
        )
        
        if analysis['success']:
            tokens = analysis['usage']['total_tokens']
            content = analysis['analysis'][:80]
            print(f"   ✅ {tokens} tokens - {content}...")
            results[detail] = tokens
        else:
            print(f"   ❌ 失败: {analysis.get('error')}")
    
    # 显示对比结果
    if results:
        print("\n📊 Token 消耗对比:")
        for detail, tokens in results.items():
            print(f"   {detail:>4}: {tokens} tokens")

def example_complete_workflow():
    """完整工作流示例"""
    print("\n🔍 示例3: 完整视频分析工作流")
    print("-" * 40)
    
    video_path = "videos/785023.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ 示例视频不存在: {video_path}")
        return
    
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        print("⚠️  Azure OpenAI 未配置，跳过完整工作流演示")
        return
    
    print("🎬 使用完整工作流函数...")
    
    # 使用完整工作流函数，包含detail参数
    result = analyze_video_with_azure_openai(
        video_path=video_path,
        k=3,
        resolution="720p",
        custom_prompt="请详细分析这个视频的内容和主要场景。",
        detail="high",  # 使用高精度模式
        adaptive_mode="adaptive"
    )
    
    if result['success']:
        analysis = result['video_analysis']
        extraction = result['keyframe_extraction']
        
        print(f"✅ 分析完成")
        print(f"📊 提取了 {extraction['extracted_frames']} 帧")
        print(f"🔍 使用 {analysis['usage']['total_tokens']} tokens")
        print(f"📝 分析结果: {analysis['analysis'][:100]}...")
    else:
        print(f"❌ 分析失败: {result.get('error')}")

def main():
    print("🎯 Azure OpenAI detail 参数功能演示")
    print("=" * 50)
    
    # 基础使用说明
    example_basic_usage()
    
    # 效果对比
    example_comparison()
    
    # 完整工作流
    example_complete_workflow()
    
    print("\n💡 最佳实践建议:")
    print("1. 批量处理时使用 detail='low' 节省成本")
    print("2. 需要精细识别时使用 detail='high'")
    print("3. 不确定时使用 detail='auto' 让系统自动选择")
    print("4. 可以根据图像复杂度动态调整 detail 参数")
    
    print("\n🎉 演示完成！")

if __name__ == "__main__":
    main()
