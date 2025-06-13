#!/usr/bin/env python3
"""
快速基准测试工具 - 专注于核心性能测试
"""

import time
import psutil
import os
import sys
from pathlib import Path
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from smart_keyframe_extractor.extractor import extract_top_k_keyframes


class QuickBenchmark:
    """快速基准测试类"""
    
    def __init__(self):
        self.results = []
    
    def benchmark_video(self, video_path: str, test_name: str = "default") -> dict:
        """对单个视频进行基准测试"""
        if not os.path.exists(video_path):
            return {"error": f"视频文件不存在: {video_path}"}
        
        print(f"\n🔧 测试: {test_name}")
        print(f"📁 视频: {video_path}")
        
        # 获取视频基本信息
        import cv2
        cap = cv2.VideoCapture(video_path)
        video_info = {
            "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        }
        video_info["duration"] = video_info["total_frames"] / video_info["fps"] if video_info["fps"] > 0 else 0
        cap.release()
        
        print(f"📹 视频信息: {video_info['width']}x{video_info['height']}, "
              f"{video_info['total_frames']} 帧, {video_info['duration']:.1f}秒")
        
        # 监控资源使用
        process = psutil.Process()
        memory_before = process.memory_info().rss / (1024**2)  # MB
        
        start_time = time.time()
        
        try:
            # 执行关键帧提取
            result = extract_top_k_keyframes(
                video_path=video_path,
                k=5,
                resolution='original',
                return_base64=False,
                save_files=False
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            memory_after = process.memory_info().rss / (1024**2)  # MB
            
            # 分析结果
            success = 'frames' in result and len(result['frames']) > 0
            keyframes_count = len(result.get('frames', []))
            
            benchmark_result = {
                "test_name": test_name,
                "video_path": video_path,
                "video_info": video_info,
                "execution_time": execution_time,
                "memory_usage": memory_after - memory_before,
                "success": success,
                "keyframes_extracted": keyframes_count,
                "processing_fps": video_info['total_frames'] / execution_time if execution_time > 0 else 0,
                "efficiency_score": keyframes_count / execution_time if execution_time > 0 else 0,
                "timestamp": datetime.now().isoformat(),
                "error": None
            }
            
            print(f"✅ 测试完成:")
            print(f"   ⏱️  执行时间: {execution_time:.2f}s")
            print(f"   💾 内存使用: {benchmark_result['memory_usage']:.1f}MB")
            print(f"   🎯 提取帧数: {keyframes_count}")
            print(f"   🚀 处理速度: {benchmark_result['processing_fps']:.1f} fps")
            print(f"   📊 效率分数: {benchmark_result['efficiency_score']:.2f} 帧/秒")
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            benchmark_result = {
                "test_name": test_name,
                "video_path": video_path,
                "video_info": video_info,
                "execution_time": execution_time,
                "memory_usage": 0,
                "success": False,
                "keyframes_extracted": 0,
                "processing_fps": 0,
                "efficiency_score": 0,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            
            print(f"❌ 测试失败: {e}")
        
        self.results.append(benchmark_result)
        return benchmark_result
    
    def compare_configurations(self, video_path: str) -> list:
        """对比不同配置的性能"""
        print(f"\n🔄 对比不同配置...")
        
        configs = [
            {"k": 3, "resolution": "original", "name": "原始分辨率_3帧"},
            {"k": 5, "resolution": "original", "name": "原始分辨率_5帧"},
            {"k": 10, "resolution": "original", "name": "原始分辨率_10帧"},
            {"k": 5, "resolution": "720p", "name": "720p分辨率_5帧"},
            {"k": 5, "resolution": "480p", "name": "480p分辨率_5帧"},
        ]
        
        comparison_results = []
        
        for config in configs:
            print(f"\n🔧 测试配置: {config['name']}")
            
            start_time = time.time()
            
            try:
                result = extract_top_k_keyframes(
                    video_path=video_path,
                    k=config['k'],
                    resolution=config['resolution'],
                    return_base64=False,
                    save_files=False
                )
                
                execution_time = time.time() - start_time
                success = 'frames' in result and len(result['frames']) > 0
                keyframes_count = len(result.get('frames', []))
                
                config_result = {
                    "config": config,
                    "execution_time": execution_time,
                    "success": success,
                    "keyframes_extracted": keyframes_count,
                    "efficiency": keyframes_count / execution_time if execution_time > 0 else 0
                }
                
                print(f"   ⏱️  {execution_time:.2f}s, 🎯 {keyframes_count}帧, 📊 {config_result['efficiency']:.2f}帧/秒")
                
            except Exception as e:
                config_result = {
                    "config": config,
                    "execution_time": time.time() - start_time,
                    "success": False,
                    "keyframes_extracted": 0,
                    "efficiency": 0,
                    "error": str(e)
                }
                print(f"   ❌ 失败: {e}")
            
            comparison_results.append(config_result)
        
        # 显示对比结果
        print(f"\n📊 配置对比结果:")
        print(f"{'配置':<20} {'时间(s)':<10} {'帧数':<8} {'效率(帧/s)':<12} {'状态'}")
        print("-" * 60)
        
        for result in comparison_results:
            status = "✅" if result['success'] else "❌"
            print(f"{result['config']['name']:<20} "
                  f"{result['execution_time']:<10.2f} "
                  f"{result['keyframes_extracted']:<8} "
                  f"{result['efficiency']:<12.2f} "
                  f"{status}")
        
        return comparison_results
    
    def save_results(self, filename: str = None):
        """保存测试结果"""
        if not filename:
            filename = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_dir = Path("benchmark_results")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 结果已保存到: {output_file}")


def main():
    """主函数"""
    print("🚀 Smart Keyframe Extractor - 快速基准测试")
    print("=" * 50)
    
    benchmark = QuickBenchmark()
    
    # 检查是否有测试视频
    test_video = "videos/785023.mp4"
    if not os.path.exists(test_video):
        print(f"❌ 测试视频不存在: {test_video}")
        print("请将测试视频放在 videos/ 目录下")
        return
    
    try:
        # 1. 基本基准测试
        print("\n📈 步骤 1: 基本性能测试")
        benchmark.benchmark_video(test_video, "基本性能测试")
        
        # 2. 配置对比测试
        print("\n📈 步骤 2: 配置对比测试")
        comparison_results = benchmark.compare_configurations(test_video)
        
        # 3. 保存结果
        benchmark.save_results()
        
        print("\n🎉 基准测试完成！")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
