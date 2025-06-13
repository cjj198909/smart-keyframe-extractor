#!/usr/bin/env python3
"""
多视频文件夹压力测试脚本
专门用于处理大量视频文件的并发压力测试
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.cloud_stress_test import run_cloud_stress_test


def setup_wyze_ai_test():
    """设置Wyze AI视频测试"""
    
    # 你的视频文件夹路径
    video_dirs = [
        "/Users/jiajunchen/Code/wyze-ai/insight_videos"
    ]
    
    print("🎬 Wyze AI 智能视频分析 - 大规模压力测试")
    print("=" * 60)
    
    # 检查视频目录
    valid_dirs = []
    total_videos = 0
    
    for video_dir in video_dirs:
        if os.path.exists(video_dir):
            video_path = Path(video_dir)
            video_files = list(video_path.glob("**/*.mp4")) + \
                         list(video_path.glob("**/*.avi")) + \
                         list(video_path.glob("**/*.mov"))
            
            print(f"✅ 视频目录: {video_dir}")
            print(f"   📹 发现视频文件: {len(video_files)} 个")
            
            valid_dirs.append(video_dir)
            total_videos += len(video_files)
        else:
            print(f"❌ 视频目录不存在: {video_dir}")
    
    if not valid_dirs:
        print("\n❌ 没有有效的视频目录，请检查路径")
        return
    
    print(f"\n📊 测试规模: {total_videos} 个视频文件")
    
    # 选择测试模式
    print("\n请选择测试模式:")
    print("1. 快速验证测试 (minimal)")
    print("2. 标准并发测试 (standard)")
    print("3. 全面压力测试 (comprehensive)")
    print("4. 极限压力测试 (stress)")
    print("5. 持续负载测试 (sustained)")
    print("6. 自定义测试")
    
    choice = input("\n请选择 (1-6): ").strip()
    
    # 构建测试命令参数
    base_args = [
        "--video-dirs", *valid_dirs,
        "--output-dir", "wyze_stress_results"
    ]
    
    if choice == "1":
        # 快速验证
        test_args = base_args + [
            "--test-profile", "minimal",
            "--max-workers", "4",
            "--iterations", "1"
        ]
        print("\n🚀 启动快速验证测试...")
        
    elif choice == "2":
        # 标准并发测试
        workers = input("请输入并发数 (默认8): ") or "8"
        iterations = input("请输入迭代次数 (默认2): ") or "2"
        
        test_args = base_args + [
            "--test-profile", "standard",
            "--max-workers", workers,
            "--iterations", iterations
        ]
        print(f"\n🚀 启动标准并发测试 ({workers}并发, {iterations}迭代)...")
        
    elif choice == "3":
        # 全面压力测试
        workers = input("请输入并发数 (默认16): ") or "16"
        
        test_args = base_args + [
            "--test-profile", "comprehensive",
            "--max-workers", workers,
            "--iterations", "1"
        ]
        print(f"\n🚀 启动全面压力测试 ({workers}并发)...")
        
    elif choice == "4":
        # 极限压力测试
        workers = input("请输入并发数 (默认32): ") or "32"
        
        test_args = base_args + [
            "--test-profile", "stress",
            "--max-workers", workers,
            "--iterations", "3"
        ]
        print(f"\n🚀 启动极限压力测试 ({workers}并发)...")
        
    elif choice == "5":
        # 持续负载测试
        duration = input("请输入测试时长(分钟, 默认30): ") or "30"
        qps = input("请输入目标QPS (默认3.0): ") or "3.0"
        
        test_args = base_args + [
            "--test-mode", "sustained",
            "--duration", duration,
            "--target-qps", qps
        ]
        print(f"\n🚀 启动持续负载测试 ({duration}分钟, {qps}QPS)...")
        
    elif choice == "6":
        # 自定义测试
        print("\n⚙️ 自定义测试配置:")
        profile = input("测试档案 (minimal/standard/comprehensive/stress): ") or "standard"
        workers = input("并发数: ") or "8"
        iterations = input("迭代次数: ") or "1"
        mode = input("测试模式 (concurrent/sustained/both): ") or "concurrent"
        
        test_args = base_args + [
            "--test-profile", profile,
            "--max-workers", workers,
            "--iterations", iterations,
            "--test-mode", mode
        ]
        
        if mode in ["sustained", "both"]:
            duration = input("持续测试时长(分钟): ") or "15"
            qps = input("目标QPS: ") or "2.0"
            test_args.extend(["--duration", duration, "--target-qps", qps])
        
        print(f"\n🚀 启动自定义测试...")
        
    else:
        print("❌ 无效选择")
        return
    
    # 确认开始测试
    print(f"\n⚠️ 即将开始测试 {total_videos} 个视频文件")
    print("测试过程中会占用大量系统资源")
    
    confirm = input("确认开始测试? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ 测试已取消")
        return
    
    # 模拟命令行参数
    import sys
    original_argv = sys.argv
    try:
        sys.argv = ['cloud_stress_test.py'] + test_args
        run_cloud_stress_test()
    finally:
        sys.argv = original_argv


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Wyze AI 多视频文件夹压力测试')
    parser.add_argument('--auto', action='store_true', 
                       help='自动运行标准测试')
    parser.add_argument('--workers', type=int, default=8,
                       help='并发数 (默认8)')
    parser.add_argument('--profile', default='standard',
                       choices=['minimal', 'standard', 'comprehensive', 'stress'],
                       help='测试档案')
    
    args = parser.parse_args()
    
    if args.auto:
        # 自动模式
        video_dirs = ["/Users/jiajunchen/Code/wyze-ai/insight_videos"]
        
        import sys
        test_args = [
            '--video-dirs', *video_dirs,
            '--test-profile', args.profile,
            '--max-workers', str(args.workers),
            '--iterations', '1',
            '--output-dir', 'wyze_auto_results'
        ]
        
        original_argv = sys.argv
        try:
            sys.argv = ['cloud_stress_test.py'] + test_args
            run_cloud_stress_test()
        finally:
            sys.argv = original_argv
    else:
        # 交互模式
        setup_wyze_ai_test()


if __name__ == "__main__":
    main()
