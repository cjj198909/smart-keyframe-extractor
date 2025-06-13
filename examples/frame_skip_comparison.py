#!/usr/bin/env python3
"""
跳帧方式对比演示
比较参数化前后的跳帧功能区别
"""

import time
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_keyframe_extractor.extractor import extract_top_k_keyframes

def demonstrate_frame_skip_evolution():
    """演示跳帧功能的演进"""
    
    video_path = "/Users/jiajunchen/Code/smart_frame/videos/785023.mp4"
    
    if not os.path.exists(video_path):
        print("❌ 演示视频不存在")
        return
    
    print("🎬 跳帧功能演进对比演示")
    print("=" * 60)
    
    # 1. 模拟原来的方式（固定参数）
    print("\n📊 原来的方式（固定跳帧）:")
    print("- 用户无法控制跳帧参数")
    print("- 始终分析所有帧 (相当于 frame_skip=1)")
    print("- 无性能优化选项")
    
    start_time = time.time()
    result_original = extract_top_k_keyframes(
        video_path=video_path,
        k=5,
        frame_skip=1,  # 模拟原来的固定值
        return_base64=False,
        save_files=False
    )
    original_time = time.time() - start_time
    
    print(f"⏱️  处理时间: {original_time:.2f}秒")
    print(f"🎯 提取帧数: {len(result_original.get('keyframes', []))}")
    
    # 2. 现在的参数化方式
    print("\n🚀 现在的参数化方式:")
    print("- 用户完全可控跳帧参数")
    print("- 可根据需求调整性能/精度平衡")
    print("- 支持多种跳帧策略")
    
    frame_skip_options = [2, 3, 5]
    
    for frame_skip in frame_skip_options:
        print(f"\n   📈 测试 frame_skip={frame_skip}:")
        start_time = time.time()
        
        result_optimized = extract_top_k_keyframes(
            video_path=video_path,
            k=5,
            frame_skip=frame_skip,
            return_base64=False,
            save_files=False
        )
        
        optimized_time = time.time() - start_time
        speedup = original_time / optimized_time if optimized_time > 0 else 0
        
        print(f"      ⏱️  处理时间: {optimized_time:.2f}秒")
        print(f"      🚀 加速比例: {speedup:.2f}x")
        print(f"      🎯 提取帧数: {len(result_optimized.get('keyframes', []))}")
    
    # 3. 功能对比总结
    print("\n" + "=" * 60)
    print("📋 功能对比总结:")
    print("原来方式:")
    print("  ❌ 固定跳帧策略")
    print("  ❌ 无用户控制接口")
    print("  ❌ 无性能优化选项")
    print("  ❌ 无CLI支持")
    
    print("\n参数化后:")
    print("  ✅ 灵活的跳帧控制")
    print("  ✅ 完整的用户接口")
    print("  ✅ 多级性能优化")
    print("  ✅ CLI和API双重支持")
    print("  ✅ 详细的使用文档")

def demonstrate_cli_evolution():
    """演示CLI功能的演进"""
    
    print("\n🖥️  命令行界面演进:")
    print("=" * 40)
    
    print("原来的CLI（无跳帧控制）:")
    print("```bash")
    print("python -m smart_keyframe_extractor.cli video.mp4")
    print("# 只能使用固定的分析精度")
    print("```")
    
    print("\n现在的CLI（完整跳帧控制）:")
    print("```bash")
    print("# 标准精度")
    print("python -m smart_keyframe_extractor.cli video.mp4")
    print()
    print("# 平衡模式")
    print("python -m smart_keyframe_extractor.cli --frame-skip 2 video.mp4")
    print()
    print("# 快速模式")
    print("python -m smart_keyframe_extractor.cli --frame-skip 3 video.mp4")
    print()
    print("# 超快速模式")
    print("python -m smart_keyframe_extractor.cli --frame-skip 5 video.mp4")
    print("```")

if __name__ == "__main__":
    demonstrate_frame_skip_evolution()
    demonstrate_cli_evolution()
    
    print("\n🎉 参数化跳帧功能让用户可以:")
    print("   1. 🎯 根据视频类型调整分析精度")
    print("   2. ⚡ 根据性能需求优化处理速度")
    print("   3. 🔧 通过CLI和API灵活控制")
    print("   4. 📊 获得详细的处理反馈")
