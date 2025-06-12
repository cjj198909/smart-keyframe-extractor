#!/usr/bin/env python3
"""
使用示例脚本
展示如何使用 smart-keyframe-extractor
"""

import os
import sys
from smart_keyframe_extractor import extract_top_k_keyframes
from smart_keyframe_extractor.azure_openai import analyze_video_with_azure_openai


def basic_extraction_example():
    """基础关键帧提取示例"""
    print("=== 基础关键帧提取示例 ===")
    
    # 假设有一个测试视频文件
    video_path = "test_video.mp4"
    
    if not os.path.exists(video_path):
        print(f"请先准备测试视频文件: {video_path}")
        return
    
    # 提取5帧，720p分辨率，返回base64
    result = extract_top_k_keyframes(
        video_path=video_path,
        k=5,
        resolution="720p",
        return_base64=True,
        save_files=False
    )
    
    if 'error' in result:
        print(f"提取失败: {result['error']}")
        return
    
    print(f"成功提取 {result['extracted_frames']} 帧")
    print(f"视频时长: {result['video_duration']:.1f}秒")
    print(f"原始分辨率: {result['original_resolution']}")
    
    for i, frame in enumerate(result['frames']):
        print(f"帧 {i+1}: 时间 {frame['timestamp']:.1f}s, "
              f"变化分数 {frame['change_score']:.1f}, "
              f"Base64长度 {len(frame['base64'])}")


def adaptive_mode_example():
    """自适应模式示例"""
    print("\n=== 自适应模式示例 ===")
    
    video_path = "test_video.mp4"
    
    if not os.path.exists(video_path):
        print(f"请先准备测试视频文件: {video_path}")
        return
    
    # 自适应模式 - 根据视频长度自动决定帧数
    result = extract_top_k_keyframes(
        video_path=video_path,
        k="auto",
        adaptive_mode="adaptive",
        min_frames=3,
        max_frames=15,
        resolution="480p",
        return_base64=True
    )
    
    if 'error' in result:
        print(f"提取失败: {result['error']}")
        return
    
    print(f"自适应计算结果: {result['calculated_frames']} 帧")
    print(f"实际提取: {result['extracted_frames']} 帧")


def interval_mode_example():
    """间隔模式示例"""
    print("\n=== 间隔模式示例 ===")
    
    video_path = "test_video.mp4"
    
    if not os.path.exists(video_path):
        print(f"请先准备测试视频文件: {video_path}")
        return
    
    # 每10秒提取1帧
    result = extract_top_k_keyframes(
        video_path=video_path,
        adaptive_mode="interval",
        interval=10.0,
        frames_per_interval=1,
        resolution="720p",
        return_base64=True
    )
    
    if 'error' in result:
        print(f"提取失败: {result['error']}")
        return
    
    print(f"间隔模式提取 {result['extracted_frames']} 帧")
    for frame in result['frames']:
        print(f"  时间: {frame['timestamp']:.1f}s")


def save_files_example():
    """保存文件示例"""
    print("\n=== 保存文件示例 ===")
    
    video_path = "test_video.mp4"
    output_dir = "output_frames"
    
    if not os.path.exists(video_path):
        print(f"请先准备测试视频文件: {video_path}")
        return
    
    # 同时保存文件和返回base64
    result = extract_top_k_keyframes(
        video_path=video_path,
        output_dir=output_dir,
        k=6,
        resolution="720p",
        return_base64=True,
        save_files=True
    )
    
    if 'error' in result:
        print(f"提取失败: {result['error']}")
        return
    
    print(f"文件保存到: {result['output_dir']}")
    for frame in result['frames']:
        if 'filename' in frame:
            print(f"  {frame['filename']}: {frame['resolution']}")


def azure_openai_example():
    """Azure OpenAI分析示例"""
    print("\n=== Azure OpenAI分析示例 ===")
    
    # 检查环境变量
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if not api_key or not endpoint:
        print("请设置Azure OpenAI环境变量:")
        print("export AZURE_OPENAI_API_KEY='your-api-key'")
        print("export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        return
    
    video_path = "test_video.mp4"
    
    if not os.path.exists(video_path):
        print(f"请先准备测试视频文件: {video_path}")
        return
    
    # 完整的视频分析流程
    result = analyze_video_with_azure_openai(
        video_path=video_path,
        k=5,
        resolution="720p",
        custom_prompt="请详细分析这个视频的内容和主要场景"
    )
    
    if result['success']:
        print("AI分析成功!")
        print(f"提取了 {result['keyframe_extraction']['extracted_frames']} 帧")
        print(f"使用token数: {result['video_analysis']['usage']['total_tokens']}")
        print("\nAI分析结果:")
        print("-" * 50)
        print(result['video_analysis']['analysis'])
    else:
        print(f"分析失败: {result['error']}")
        if 'keyframe_extraction' in result:
            print("关键帧提取成功，但AI分析失败")


def batch_processing_example():
    """批量处理示例"""
    print("\n=== 批量处理示例 ===")
    
    video_files = ["test_video1.mp4", "test_video2.mp4"]
    
    # 检查文件是否存在
    existing_files = [f for f in video_files if os.path.exists(f)]
    
    if not existing_files:
        print(f"请先准备测试视频文件: {video_files}")
        return
    
    results = []
    
    for video_file in existing_files:
        print(f"处理: {video_file}")
        result = extract_top_k_keyframes(
            video_path=video_file,
            k=3,
            resolution="480p",
            return_base64=True
        )
        
        if 'error' not in result:
            results.append(result)
            print(f"  成功提取 {result['extracted_frames']} 帧")
        else:
            print(f"  失败: {result['error']}")
    
    print(f"\n批量处理完成，共处理 {len(results)} 个视频")


def main():
    """主函数"""
    print("Smart Keyframe Extractor 使用示例")
    print("=" * 50)
    
    # 运行各种示例
    basic_extraction_example()
    adaptive_mode_example()
    interval_mode_example()
    save_files_example()
    
    # Azure OpenAI示例（需要配置环境变量）
    azure_openai_example()
    
    # 批量处理示例
    batch_processing_example()
    
    print("\n所有示例运行完成!")
    print("\n提示: 要运行这些示例，请准备一个名为 'test_video.mp4' 的测试视频文件")


if __name__ == "__main__":
    main()
