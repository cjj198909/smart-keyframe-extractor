#!/usr/bin/env python3
"""
Azure Blob Storage视频处理测试脚本
测试从Azure Blob下载视频并提取关键帧
"""

import os
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from smart_keyframe_extractor.extractor import extract_top_k_keyframes
    from smart_keyframe_extractor.remote_video_utils import is_remote_url, get_video_url_info
    print("✅ 成功导入所有模块")
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)

def test_azure_blob_video_processing():
    """测试Azure Blob视频处理"""
    # Azure Blob视频URL
    blob_url = "https://studysa2024.blob.core.windows.net/wyze/insight_videos/785490.mp4"
    
    print(f"🎬 开始测试Azure Blob视频: {blob_url}")
    print("=" * 80)
    
    # 1. 验证URL检测
    print("1. URL检测测试:")
    is_remote = is_remote_url(blob_url)
    print(f"   是否为远程URL: {is_remote}")
    
    if is_remote:
        url_info = get_video_url_info(blob_url)
        print(f"   存储类型: {url_info['storage_type']}")
        print(f"   主机名: {url_info['hostname']}")
        print(f"   路径: {url_info['path']}")
        print(f"   格式: {url_info['format']}")
    
    print()
    
    # 2. 创建输出目录
    output_dir = project_root / "output_azure_blob_test"
    output_dir.mkdir(exist_ok=True)
    
    print(f"2. 输出目录: {output_dir}")
    print()
    
    # 3. 测试不同提取模式
    test_cases = [
        {
            "mode": "fixed",
            "params": {"k": 5, "output_dir": str(output_dir / "fixed")},
            "description": "固定模式 - 提取5个关键帧"
        },
        {
            "mode": "interval", 
            "params": {"k": 3, "interval": 2.0, "output_dir": str(output_dir / "interval")},
            "description": "间隔模式 - 每2秒提取，最多3帧"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"3.{i} {test_case['description']}:")
        start_time = time.time()
        
        try:
            if test_case["mode"] == "fixed":
                results = extract_top_k_keyframes(
                    video_path=blob_url,
                    k=test_case["params"]["k"],
                    output_dir=test_case["params"]["output_dir"],
                    save_files=True,
                    return_base64=False
                )
            else:  # interval mode
                results = extract_top_k_keyframes(
                    video_path=blob_url,
                    k=test_case["params"]["k"],
                    adaptive_mode="interval",
                    interval=test_case["params"]["interval"],
                    output_dir=test_case["params"]["output_dir"],
                    save_files=True,
                    return_base64=False
                )
            
            elapsed_time = time.time() - start_time
            
            if 'error' in results:
                print(f"   ❌ 处理失败: {results['error']}")
                print(f"   失败时间: {elapsed_time:.2f}秒")
            else:
                keyframes = results.get('keyframes', [])
                print(f"   ✅ 处理成功！")
                print(f"   处理时间: {elapsed_time:.2f}秒")
                print(f"   提取帧数: {len(keyframes)}")
                
                # 显示结果详情
                for j, frame in enumerate(keyframes):
                    output_path = frame.get('output_path', '')
                    if output_path and os.path.exists(output_path):
                        file_size = os.path.getsize(output_path) / 1024  # KB
                        print(f"   帧{j+1}: 时间={frame['timestamp']:.2f}s, "
                              f"得分={frame.get('score', 'N/A'):.4f}, "
                              f"文件大小={file_size:.1f}KB")
                    else:
                        print(f"   帧{j+1}: 时间={frame['timestamp']:.2f}s, "
                              f"得分={frame.get('score', 'N/A'):.4f}")
            
            print()
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"   ❌ 处理异常: {e}")
            print(f"   异常时间: {elapsed_time:.2f}秒")
            print()
    
    # 4. 检查缓存状态
    print("4. 缓存状态检查:")
    cache_dirs = [
        Path.home() / ".cache" / "smart_keyframe_cache",
        Path("/tmp") / "smart_keyframe_cache",
        Path("/var/folders").glob("*/*/T/smart_keyframe_cache")
    ]
    
    cache_found = False
    for cache_path in cache_dirs:
        if isinstance(cache_path, Path) and cache_path.exists():
            cache_files = list(cache_path.glob("*"))
            if cache_files:
                cache_size = sum(f.stat().st_size for f in cache_files if f.is_file())
                print(f"   缓存目录: {cache_path}")
                print(f"   缓存文件数量: {len(cache_files)}")
                print(f"   缓存总大小: {cache_size / 1024 / 1024:.2f} MB")
                
                for cache_file in cache_files:
                    if cache_file.is_file():
                        file_size = cache_file.stat().st_size / 1024 / 1024  # MB
                        print(f"   - {cache_file.name}: {file_size:.2f} MB")
                cache_found = True
                break
    
    if not cache_found:
        print("   未找到缓存文件")
    
    print()
    print("🎉 Azure Blob视频处理测试完成！")

if __name__ == "__main__":
    test_azure_blob_video_processing()
