#!/usr/bin/env python3
"""
S3视频处理测试脚本
测试从S3下载视频并提取关键帧
"""

import os
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from smart_keyframe_extractor import SmartKeyFrameExtractor
    from smart_keyframe_extractor.remote_video_utils import is_remote_url, get_video_url_info
    print("✅ 成功导入所有模块")
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)

def test_s3_video_processing():
    """测试S3视频处理"""
    # S3视频URL
    s3_url = "s3://video-test-2506/787037.mp4"
    
    print(f"🎬 开始测试S3视频: {s3_url}")
    print("=" * 60)
    
    # 1. 验证URL检测
    print("1. URL检测测试:")
    is_remote = is_remote_url(s3_url)
    print(f"   是否为远程URL: {is_remote}")
    
    if is_remote:
        url_info = get_video_url_info(s3_url)
        print(f"   URL信息: {url_info}")
    
    print()
    
    # 2. 创建提取器实例
    print("2. 创建Smart Keyframe Extractor:")
    cache_dir = project_root / "cache"
    output_dir = project_root / "output_s3_test"
    output_dir.mkdir(exist_ok=True)
    
    extractor = SmartKeyFrameExtractor(
        enable_remote=True,
        cache_dir=str(cache_dir)
    )
    print(f"   ✅ 提取器创建成功")
    print(f"   缓存目录: {cache_dir}")
    print(f"   输出目录: {output_dir}")
    print()
    
    # 3. 测试不同提取模式
    test_cases = [
        {
            "mode": "adaptive",
            "params": {"k": 5, "output_dir": str(output_dir / "adaptive")},
            "description": "自适应模式 - 提取5个关键帧"
        },
        {
            "mode": "interval",
            "params": {"k": 3, "interval": 1.0, "output_dir": str(output_dir / "interval")},
            "description": "间隔模式 - 每1秒提取，最多3帧"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"3.{i} {test_case['description']}:")
        start_time = time.time()
        
        try:
            if test_case["mode"] == "adaptive":
                results = extractor.extract_top_k_keyframes(
                    video_path=s3_url,
                    k=test_case["params"]["k"],
                    output_dir=test_case["params"]["output_dir"]
                )
            else:  # interval mode
                results = extractor.extract_keyframes_by_interval(
                    video_path=s3_url,
                    interval=test_case["params"]["interval"],
                    max_frames=test_case["params"]["k"],
                    output_dir=test_case["params"]["output_dir"]
                )
            
            elapsed_time = time.time() - start_time
            
            print(f"   ✅ 处理成功！")
            print(f"   处理时间: {elapsed_time:.2f}秒")
            print(f"   提取帧数: {len(results)}")
            
            # 显示结果详情
            for j, result in enumerate(results):
                file_size = os.path.getsize(result['output_path']) / 1024  # KB
                print(f"   帧{j+1}: 时间={result['timestamp']:.2f}s, "
                      f"得分={result.get('score', 'N/A'):.4f}, "
                      f"文件大小={file_size:.1f}KB")
            
            print()
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"   ❌ 处理失败: {e}")
            print(f"   失败时间: {elapsed_time:.2f}秒")
            print()
    
    # 4. 检查缓存状态
    print("4. 缓存状态检查:")
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*"))
        cache_size = sum(f.stat().st_size for f in cache_files if f.is_file())
        print(f"   缓存文件数量: {len(cache_files)}")
        print(f"   缓存总大小: {cache_size / 1024 / 1024:.2f} MB")
        
        for cache_file in cache_files:
            if cache_file.is_file():
                file_size = cache_file.stat().st_size / 1024 / 1024  # MB
                print(f"   - {cache_file.name}: {file_size:.2f} MB")
    else:
        print("   缓存目录不存在")
    
    print()
    print("🎉 S3视频处理测试完成！")

if __name__ == "__main__":
    test_s3_video_processing()
