#!/usr/bin/env python3
"""
Smart Keyframe Extractor - 压力测试和基准测试工具
测试不同视频条件下的性能表现和内存使用情况
"""

import time
import psutil
import os
import sys
import threading
import statistics
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import pandas as pd
import tempfile
import subprocess
import cv2

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from smart_keyframe_extractor.extractor import extract_top_k_keyframes, SmartKeyFrameExtractor


class BenchmarkTester:
    """压力测试和基准测试类"""
    
    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
        self.system_info = self._get_system_info()
        self.test_videos = []
        
        print(f"🚀 压力测试工具初始化完成")
        print(f"📁 结果输出目录: {self.output_dir}")
        print(f"💻 系统信息: {self.system_info}")
    
    def _get_system_info(self) -> Dict:
        """获取系统信息"""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else "Unknown",
            "memory_total": psutil.virtual_memory().total / (1024**3),  # GB
            "python_version": sys.version,
            "opencv_version": cv2.__version__,
            "timestamp": datetime.now().isoformat()
        }
    
    def create_test_videos(self) -> List[str]:
        """创建不同规格的测试视频"""
        print("\n🎬 创建测试视频...")
        
        test_specs = [
            {"resolution": "640x480", "duration": 10, "fps": 15, "name": "small_short"},
            {"resolution": "640x480", "duration": 30, "fps": 30, "name": "small_medium"},
            {"resolution": "1280x720", "duration": 15, "fps": 24, "name": "hd_short"},
            {"resolution": "1280x720", "duration": 60, "fps": 30, "name": "hd_long"},
            {"resolution": "1920x1080", "duration": 20, "fps": 30, "name": "fhd_medium"},
            {"resolution": "1920x1080", "duration": 120, "fps": 60, "name": "fhd_long_highfps"},
        ]
        
        created_videos = []
        
        for spec in test_specs:
            video_path = self.output_dir / f"test_{spec['name']}.mp4"
            
            if video_path.exists():
                print(f"✅ 测试视频已存在: {video_path}")
                created_videos.append(str(video_path))
                continue
            
            try:
                # 使用FFmpeg创建测试视频
                cmd = [
                    "ffmpeg", "-f", "lavfi",
                    "-i", f"testsrc=duration={spec['duration']}:size={spec['resolution']}:rate={spec['fps']}",
                    "-pix_fmt", "yuv420p",
                    "-y", str(video_path)
                ]
                
                print(f"🔧 创建 {spec['name']} ({spec['resolution']}, {spec['duration']}s, {spec['fps']}fps)...")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and video_path.exists():
                    created_videos.append(str(video_path))
                    print(f"✅ 创建成功: {video_path}")
                else:
                    print(f"❌ 创建失败: {spec['name']}")
                    print(f"错误: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ 创建超时: {spec['name']}")
            except Exception as e:
                print(f"❌ 创建异常: {spec['name']}, 错误: {e}")
        
        self.test_videos = created_videos
        print(f"\n📹 成功创建 {len(created_videos)} 个测试视频")
        return created_videos
    
    def monitor_resources(self, duration: float) -> Dict:
        """监控资源使用情况"""
        cpu_samples = []
        memory_samples = []
        start_time = time.time()
        
        def collect_samples():
            while time.time() - start_time < duration:
                try:
                    cpu_samples.append(psutil.cpu_percent(interval=0.1))
                    memory_samples.append(psutil.virtual_memory().percent)
                    time.sleep(0.1)
                except:
                    break
        
        monitor_thread = threading.Thread(target=collect_samples)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return {
            "cpu_samples": cpu_samples,
            "memory_samples": memory_samples
        }
    
    def benchmark_single_test(self, video_path: str, test_config: Dict) -> Dict:
        """单个测试的基准测试"""
        print(f"\n🔧 测试: {test_config['name']}")
        print(f"📁 视频: {video_path}")
        print(f"⚙️  配置: {test_config}")
        
        # 获取视频信息
        cap = cv2.VideoCapture(video_path)
        video_info = {
            "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
        }
        cap.release()
        
        # 开始监控资源
        start_time = time.time()
        process = psutil.Process()
        memory_before = process.memory_info().rss / (1024**2)  # MB
        
        try:
            # 执行关键帧提取
            result = extract_top_k_keyframes(
                video_path=video_path,
                k=test_config.get('k', 5),
                adaptive_mode=test_config.get('adaptive_mode'),
                resolution=test_config.get('resolution', 'original'),
                return_base64=test_config.get('return_base64', False),
                save_files=False
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            memory_after = process.memory_info().rss / (1024**2)  # MB
            memory_peak = memory_after  # 简化的峰值内存估算
            
            # 分析结果
            success = 'keyframes' in result and len(result['keyframes']) > 0
            keyframes_extracted = len(result.get('keyframes', []))
            
            test_result = {
                "test_name": test_config['name'],
                "video_path": video_path,
                "video_info": video_info,
                "config": test_config,
                "execution_time": execution_time,
                "memory_before": memory_before,
                "memory_after": memory_after,
                "memory_peak": memory_peak,
                "memory_usage": memory_peak - memory_before,
                "success": success,
                "keyframes_extracted": keyframes_extracted,
                "fps_processed": video_info['total_frames'] / execution_time if execution_time > 0 else 0,
                "frames_per_second": keyframes_extracted / execution_time if execution_time > 0 else 0,
                "timestamp": datetime.now().isoformat(),
                "error": None
            }
            
            print(f"✅ 测试完成")
            print(f"⏱️  执行时间: {execution_time:.2f}s")
            print(f"💾 内存使用: {memory_usage:.1f}MB")
            print(f"🎯 提取帧数: {keyframes_extracted}")
            print(f"🚀 处理速度: {test_result['fps_processed']:.1f} fps")
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            test_result = {
                "test_name": test_config['name'],
                "video_path": video_path,
                "video_info": video_info,
                "config": test_config,
                "execution_time": execution_time,
                "memory_before": memory_before,
                "memory_after": memory_before,
                "memory_peak": memory_before,
                "memory_usage": 0,
                "success": False,
                "keyframes_extracted": 0,
                "fps_processed": 0,
                "frames_per_second": 0,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            
            print(f"❌ 测试失败: {e}")
        
        return test_result
    
    def run_comprehensive_benchmark(self) -> List[Dict]:
        """运行全面的基准测试"""
        print("\n🚀 开始全面基准测试...")
        
        # 确保有测试视频
        if not self.test_videos:
            self.create_test_videos()
        
        # 定义测试配置
        test_configs = [
            {"name": "basic_5frames", "k": 5, "resolution": "original"},
            {"name": "basic_10frames", "k": 10, "resolution": "original"},
            {"name": "adaptive_mode", "k": "auto", "adaptive_mode": "adaptive", "resolution": "original"},
            {"name": "720p_5frames", "k": 5, "resolution": "720p"},
            {"name": "480p_10frames", "k": 10, "resolution": "480p"},
            {"name": "base64_mode", "k": 5, "resolution": "720p", "return_base64": True},
        ]
        
        results = []
        total_tests = len(self.test_videos) * len(test_configs)
        current_test = 0
        
        for video_path in self.test_videos:
            for config in test_configs:
                current_test += 1
                print(f"\n📊 进度: {current_test}/{total_tests}")
                
                result = self.benchmark_single_test(video_path, config)
                results.append(result)
                self.results.append(result)
        
        # 保存结果
        self.save_results(results)
        return results
    
    def run_stress_test(self, video_path: str, iterations: int = 10) -> Dict:
        """运行压力测试"""
        print(f"\n💪 开始压力测试: {iterations} 次迭代")
        
        if not os.path.exists(video_path):
            raise ValueError(f"测试视频不存在: {video_path}")
        
        execution_times = []
        memory_usages = []
        successes = 0
        
        config = {"name": "stress_test", "k": 5, "resolution": "original"}
        
        for i in range(iterations):
            print(f"\n🔄 迭代 {i+1}/{iterations}")
            
            result = self.benchmark_single_test(video_path, {
                **config,
                "name": f"stress_test_iter_{i+1}"
            })
            
            execution_times.append(result['execution_time'])
            memory_usages.append(result['memory_usage'])
            
            if result['success']:
                successes += 1
        
        # 统计分析
        stress_result = {
            "test_type": "stress_test",
            "video_path": video_path,
            "iterations": iterations,
            "success_rate": successes / iterations,
            "execution_time": {
                "mean": statistics.mean(execution_times),
                "median": statistics.median(execution_times),
                "min": min(execution_times),
                "max": max(execution_times),
                "std": statistics.stdev(execution_times) if len(execution_times) > 1 else 0
            },
            "memory_usage": {
                "mean": statistics.mean(memory_usages),
                "median": statistics.median(memory_usages),
                "min": min(memory_usages),
                "max": max(memory_usages),
                "std": statistics.stdev(memory_usages) if len(memory_usages) > 1 else 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n📊 压力测试结果:")
        print(f"✅ 成功率: {stress_result['success_rate']*100:.1f}%")
        print(f"⏱️  平均执行时间: {stress_result['execution_time']['mean']:.2f}s")
        print(f"💾 平均内存使用: {stress_result['memory_usage']['mean']:.1f}MB")
        
        return stress_result
    
    def save_results(self, results: List[Dict]):
        """保存测试结果"""
        # JSON格式
        json_file = self.output_dir / f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "system_info": self.system_info,
                "results": results
            }, f, indent=2, ensure_ascii=False)
        
        # CSV格式
        csv_file = self.output_dir / f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df = pd.DataFrame(results)
        df.to_csv(csv_file, index=False)
        
        print(f"\n💾 结果已保存:")
        print(f"📄 JSON: {json_file}")
        print(f"📊 CSV: {csv_file}")
    
    def generate_report(self, results: List[Dict]):
        """生成性能报告"""
        print("\n📊 生成性能报告...")
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 执行时间对比
        test_names = [r['test_name'] for r in results if r['success']]
        execution_times = [r['execution_time'] for r in results if r['success']]
        
        axes[0, 0].bar(range(len(test_names)), execution_times)
        axes[0, 0].set_title('执行时间对比')
        axes[0, 0].set_ylabel('时间 (秒)')
        axes[0, 0].set_xticks(range(len(test_names)))
        axes[0, 0].set_xticklabels(test_names, rotation=45)
        
        # 内存使用对比
        memory_usages = [r['memory_usage'] for r in results if r['success']]
        axes[0, 1].bar(range(len(test_names)), memory_usages)
        axes[0, 1].set_title('内存使用对比')
        axes[0, 1].set_ylabel('内存 (MB)')
        axes[0, 1].set_xticks(range(len(test_names)))
        axes[0, 1].set_xticklabels(test_names, rotation=45)
        
        # 处理速度对比
        fps_processed = [r['fps_processed'] for r in results if r['success']]
        axes[1, 0].bar(range(len(test_names)), fps_processed)
        axes[1, 0].set_title('处理速度对比 (FPS)')
        axes[1, 0].set_ylabel('帧/秒')
        axes[1, 0].set_xticks(range(len(test_names)))
        axes[1, 0].set_xticklabels(test_names, rotation=45)
        
        # 成功率统计
        success_counts = [1 if r['success'] else 0 for r in results]
        total_tests = len(results)
        success_rate = sum(success_counts) / total_tests * 100
        
        axes[1, 1].pie([success_rate, 100-success_rate], 
                      labels=[f'成功 ({success_rate:.1f}%)', f'失败 ({100-success_rate:.1f}%)'],
                      autopct='%1.1f%%')
        axes[1, 1].set_title('测试成功率')
        
        plt.tight_layout()
        
        # 保存图表
        chart_file = self.output_dir / f"benchmark_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"📊 图表已保存: {chart_file}")


def main():
    """主函数"""
    print("🚀 Smart Keyframe Extractor - 压力测试和基准测试工具")
    print("=" * 60)
    
    # 创建测试器
    tester = BenchmarkTester()
    
    # 选择测试模式
    print("\n请选择测试模式:")
    print("1. 创建测试视频")
    print("2. 综合基准测试")
    print("3. 压力测试")
    print("4. 自定义测试")
    
    try:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            tester.create_test_videos()
            
        elif choice == "2":
            results = tester.run_comprehensive_benchmark()
            tester.generate_report(results)
            
        elif choice == "3":
            # 检查是否有现有视频
            if not os.path.exists("videos/785023.mp4"):
                print("❌ 未找到测试视频，请先创建测试视频")
                return
            
            iterations = int(input("请输入压力测试迭代次数 (默认10): ") or "10")
            result = tester.run_stress_test("videos/785023.mp4", iterations)
            
        elif choice == "4":
            print("自定义测试功能开发中...")
            
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
