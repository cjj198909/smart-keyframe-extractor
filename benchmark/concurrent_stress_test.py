#!/usr/bin/env python3
"""
并发压力测试工具 - 支持多视频文件并发处理
适合云服务器大规模压力测试
"""

import time
import psutil
import os
import sys
import threading
import statistics
import json
import concurrent.futures
import queue
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import signal
from dataclasses import dataclass
import glob
import cv2

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from smart_keyframe_extractor.extractor import extract_top_k_keyframes

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestTask:
    """测试任务数据类"""
    video_path: str
    config: Dict
    task_id: str
    thread_id: int


@dataclass
class TestResult:
    """测试结果数据类"""
    task_id: str
    thread_id: int
    video_path: str
    config: Dict
    success: bool
    execution_time: float
    memory_usage: float
    keyframes_extracted: int
    error: Optional[str]
    timestamp: str
    video_size_mb: float
    video_duration: float
    fps_processed: float


class ConcurrentStressTester:
    """并发压力测试器"""
    
    def __init__(self, output_dir: str = "benchmark_results", max_workers: int = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.results = []
        self.system_info = self._get_system_info()
        self.test_videos = []
        self.stop_event = threading.Event()
        self.stats_lock = threading.Lock()
        self.task_counter = 0
        
        # 性能监控
        self.performance_monitor = PerformanceMonitor()
        
        print(f"🚀 并发压力测试器初始化完成")
        print(f"📁 结果输出目录: {self.output_dir}")
        print(f"🔧 最大并发数: {self.max_workers}")
        print(f"💻 系统信息: {self.system_info}")
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器，优雅退出"""
        logger.warning(f"收到信号 {signum}，正在停止测试...")
        self.stop_event.set()
    
    def _get_system_info(self) -> Dict:
        """获取系统信息"""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_logical_count": psutil.cpu_count(logical=True),
            "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else "Unknown",
            "memory_total": psutil.virtual_memory().total / (1024**3),  # GB
            "memory_available": psutil.virtual_memory().available / (1024**3),  # GB
            "disk_free": psutil.disk_usage('/').free / (1024**3),  # GB
            "python_version": sys.version,
            "platform": sys.platform,
            "hostname": os.uname().nodename if hasattr(os, 'uname') else "unknown",
            "timestamp": datetime.now().isoformat()
        }
    
    def discover_video_files(self, video_dirs: List[str], extensions: List[str] = None) -> List[str]:
        """发现指定目录中的视频文件"""
        if extensions is None:
            extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        
        video_files = []
        for video_dir in video_dirs:
            video_path = Path(video_dir)
            if not video_path.exists():
                logger.warning(f"视频目录不存在: {video_dir}")
                continue
            
            logger.info(f"扫描视频目录: {video_dir}")
            for ext in extensions:
                pattern = f"**/*{ext}"
                files = list(video_path.glob(pattern))
                video_files.extend([str(f) for f in files])
                logger.info(f"找到 {len(files)} 个 {ext} 文件")
        
        self.test_videos = video_files
        logger.info(f"总共发现 {len(video_files)} 个视频文件")
        return video_files
    
    def get_video_info(self, video_path: str) -> Dict:
        """获取视频文件信息"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {"error": "无法打开视频文件"}
            
            info = {
                "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "file_size_mb": os.path.getsize(video_path) / (1024 * 1024)
            }
            info["duration"] = info["total_frames"] / info["fps"] if info["fps"] > 0 else 0
            cap.release()
            return info
        except Exception as e:
            return {"error": str(e)}
    
    def process_single_video(self, task: TestTask) -> TestResult:
        """处理单个视频的测试任务"""
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] 开始处理任务 {task.task_id}: {os.path.basename(task.video_path)}")
        
        # 获取视频信息
        video_info = self.get_video_info(task.video_path)
        if "error" in video_info:
            return TestResult(
                task_id=task.task_id,
                thread_id=task.thread_id,
                video_path=task.video_path,
                config=task.config,
                success=False,
                execution_time=0.0,
                memory_usage=0.0,
                keyframes_extracted=0,
                error=video_info["error"],
                timestamp=datetime.now().isoformat(),
                video_size_mb=0.0,
                video_duration=0.0,
                fps_processed=0.0
            )
        
        # 监控资源使用
        process = psutil.Process()
        memory_before = process.memory_info().rss / (1024**2)  # MB
        
        start_time = time.time()
        
        try:
            # 执行关键帧提取
            result = extract_top_k_keyframes(
                video_path=task.video_path,
                k=task.config.get('k', 5),
                resolution=task.config.get('resolution', 'original'),
                return_base64=task.config.get('return_base64', False),
                save_files=False
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            memory_after = process.memory_info().rss / (1024**2)  # MB
            
            # 分析结果
            success = 'frames' in result and len(result['frames']) > 0
            keyframes_extracted = len(result.get('frames', []))
            
            test_result = TestResult(
                task_id=task.task_id,
                thread_id=task.thread_id,
                video_path=task.video_path,
                config=task.config,
                success=success,
                execution_time=execution_time,
                memory_usage=memory_after - memory_before,
                keyframes_extracted=keyframes_extracted,
                error=None,
                timestamp=datetime.now().isoformat(),
                video_size_mb=video_info.get('file_size_mb', 0),
                video_duration=video_info.get('duration', 0),
                fps_processed=video_info.get('total_frames', 0) / execution_time if execution_time > 0 else 0
            )
            
            logger.info(f"[{thread_name}] 任务 {task.task_id} 完成: "
                       f"{execution_time:.2f}s, {keyframes_extracted}帧")
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            test_result = TestResult(
                task_id=task.task_id,
                thread_id=task.thread_id,
                video_path=task.video_path,
                config=task.config,
                success=False,
                execution_time=execution_time,
                memory_usage=0.0,
                keyframes_extracted=0,
                error=str(e),
                timestamp=datetime.now().isoformat(),
                video_size_mb=video_info.get('file_size_mb', 0),
                video_duration=video_info.get('duration', 0),
                fps_processed=0.0
            )
            
            logger.error(f"[{thread_name}] 任务 {task.task_id} 失败: {e}")
        
        return test_result
    
    def run_concurrent_test(self, 
                           video_dirs: List[str],
                           test_configs: List[Dict],
                           iterations: int = 1,
                           max_concurrent: int = None,
                           random_order: bool = True) -> List[TestResult]:
        """运行并发压力测试"""
        
        logger.info("🚀 开始并发压力测试")
        
        # 发现视频文件
        video_files = self.discover_video_files(video_dirs)
        if not video_files:
            logger.error("未找到任何视频文件")
            return []
        
        # 生成测试任务
        tasks = []
        for iteration in range(iterations):
            for video_path in video_files:
                for config_idx, config in enumerate(test_configs):
                    task_id = f"iter_{iteration+1}_config_{config_idx+1}_video_{len(tasks)+1}"
                    task = TestTask(
                        video_path=video_path,
                        config=config,
                        task_id=task_id,
                        thread_id=len(tasks) % self.max_workers
                    )
                    tasks.append(task)
        
        # 随机打乱任务顺序
        if random_order:
            random.shuffle(tasks)
        
        total_tasks = len(tasks)
        logger.info(f"生成 {total_tasks} 个测试任务")
        logger.info(f"视频文件: {len(video_files)} 个")
        logger.info(f"配置方案: {len(test_configs)} 个")
        logger.info(f"迭代次数: {iterations} 次")
        
        # 启动性能监控
        self.performance_monitor.start()
        
        # 执行并发测试
        results = []
        start_time = time.time()
        completed_tasks = 0
        
        max_workers = max_concurrent or self.max_workers
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(self.process_single_video, task): task
                for task in tasks
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_task):
                if self.stop_event.is_set():
                    logger.warning("收到停止信号，取消剩余任务")
                    break
                
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    with self.stats_lock:
                        completed_tasks += 1
                        progress = completed_tasks / total_tasks * 100
                        elapsed = time.time() - start_time
                        eta = elapsed / completed_tasks * (total_tasks - completed_tasks) if completed_tasks > 0 else 0
                        
                        logger.info(f"进度: {completed_tasks}/{total_tasks} ({progress:.1f}%) "
                                   f"已用时: {elapsed:.1f}s, 预计剩余: {eta:.1f}s")
                
                except Exception as e:
                    logger.error(f"任务执行异常: {e}")
        
        # 停止性能监控
        self.performance_monitor.stop()
        
        total_time = time.time() - start_time
        logger.info(f"并发测试完成: {completed_tasks}/{total_tasks} 任务完成，总耗时: {total_time:.2f}s")
        
        # 保存结果
        self.results.extend(results)
        self.save_results(results, f"concurrent_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        return results
    
    def run_sustained_load_test(self,
                               video_dirs: List[str],
                               test_config: Dict,
                               duration_minutes: int = 10,
                               target_qps: float = 1.0) -> List[TestResult]:
        """运行持续负载测试"""
        
        logger.info(f"🔥 开始持续负载测试: {duration_minutes}分钟, 目标QPS: {target_qps}")
        
        # 发现视频文件
        video_files = self.discover_video_files(video_dirs)
        if not video_files:
            logger.error("未找到任何视频文件")
            return []
        
        results = []
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        task_counter = 0
        
        # 启动性能监控
        self.performance_monitor.start()
        
        def submit_task():
            nonlocal task_counter
            video_path = random.choice(video_files)
            task_id = f"sustained_load_{task_counter+1}"
            task_counter += 1
            
            task = TestTask(
                video_path=video_path,
                config=test_config,
                task_id=task_id,
                thread_id=task_counter % self.max_workers
            )
            
            return task
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            active_futures = set()
            last_submit_time = time.time()
            
            while time.time() < end_time and not self.stop_event.is_set():
                current_time = time.time()
                
                # 根据目标QPS提交新任务
                if current_time - last_submit_time >= (1.0 / target_qps):
                    if len(active_futures) < self.max_workers:
                        task = submit_task()
                        future = executor.submit(self.process_single_video, task)
                        active_futures.add(future)
                        last_submit_time = current_time
                        logger.debug(f"提交任务 {task.task_id}, 活跃任务数: {len(active_futures)}")
                
                # 收集完成的结果
                done_futures = [f for f in active_futures if f.done()]
                for future in done_futures:
                    try:
                        result = future.result()
                        results.append(result)
                        logger.info(f"任务完成: {result.task_id}, "
                                   f"耗时: {result.execution_time:.2f}s, "
                                   f"成功: {result.success}")
                    except Exception as e:
                        logger.error(f"任务执行异常: {e}")
                    
                    active_futures.remove(future)
                
                # 短暂休眠避免CPU占用过高
                time.sleep(0.01)
            
            # 等待剩余任务完成
            logger.info(f"等待 {len(active_futures)} 个剩余任务完成...")
            concurrent.futures.wait(active_futures, timeout=60)
            
            for future in active_futures:
                if future.done():
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"任务执行异常: {e}")
        
        # 停止性能监控
        self.performance_monitor.stop()
        
        total_time = time.time() - start_time
        actual_qps = len(results) / total_time if total_time > 0 else 0
        
        logger.info(f"持续负载测试完成: {len(results)} 个任务完成, "
                   f"总耗时: {total_time:.2f}s, 实际QPS: {actual_qps:.2f}")
        
        # 保存结果
        self.save_results(results, f"sustained_load_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        return results
    
    def analyze_results(self, results: List[TestResult]) -> Dict:
        """分析测试结果"""
        if not results:
            return {"error": "没有测试结果"}
        
        # 基础统计
        total_tasks = len(results)
        successful_tasks = len([r for r in results if r.success])
        failed_tasks = total_tasks - successful_tasks
        success_rate = successful_tasks / total_tasks * 100
        
        # 性能统计
        execution_times = [r.execution_time for r in results if r.success]
        memory_usages = [r.memory_usage for r in results if r.success]
        keyframes_counts = [r.keyframes_extracted for r in results if r.success]
        
        analysis = {
            "summary": {
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": success_rate
            },
            "performance": {
                "execution_time": {
                    "mean": statistics.mean(execution_times) if execution_times else 0,
                    "median": statistics.median(execution_times) if execution_times else 0,
                    "min": min(execution_times) if execution_times else 0,
                    "max": max(execution_times) if execution_times else 0,
                    "std": statistics.stdev(execution_times) if len(execution_times) > 1 else 0
                },
                "memory_usage": {
                    "mean": statistics.mean(memory_usages) if memory_usages else 0,
                    "median": statistics.median(memory_usages) if memory_usages else 0,
                    "min": min(memory_usages) if memory_usages else 0,
                    "max": max(memory_usages) if memory_usages else 0,
                    "std": statistics.stdev(memory_usages) if len(memory_usages) > 1 else 0
                },
                "keyframes_extracted": {
                    "mean": statistics.mean(keyframes_counts) if keyframes_counts else 0,
                    "median": statistics.median(keyframes_counts) if keyframes_counts else 0,
                    "min": min(keyframes_counts) if keyframes_counts else 0,
                    "max": max(keyframes_counts) if keyframes_counts else 0,
                    "total": sum(keyframes_counts)
                }
            },
            "system_performance": self.performance_monitor.get_stats(),
            "timestamp": datetime.now().isoformat()
        }
        
        return analysis
    
    def save_results(self, results: List[TestResult], filename_prefix: str):
        """保存测试结果"""
        # 将结果转换为字典格式
        results_dict = [
            {
                "task_id": r.task_id,
                "thread_id": r.thread_id,
                "video_path": r.video_path,
                "video_filename": os.path.basename(r.video_path),
                "config": r.config,
                "success": r.success,
                "execution_time": r.execution_time,
                "memory_usage": r.memory_usage,
                "keyframes_extracted": r.keyframes_extracted,
                "error": r.error,
                "timestamp": r.timestamp,
                "video_size_mb": r.video_size_mb,
                "video_duration": r.video_duration,
                "fps_processed": r.fps_processed
            }
            for r in results
        ]
        
        # 保存JSON格式
        json_file = self.output_dir / f"{filename_prefix}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "system_info": self.system_info,
                "test_config": {
                    "max_workers": self.max_workers,
                    "total_tasks": len(results)
                },
                "results": results_dict,
                "analysis": self.analyze_results(results)
            }, f, indent=2, ensure_ascii=False)
        
        # 保存CSV格式（便于Excel分析）
        try:
            import pandas as pd
            csv_file = self.output_dir / f"{filename_prefix}.csv"
            df = pd.DataFrame(results_dict)
            df.to_csv(csv_file, index=False)
            logger.info(f"结果已保存: {json_file}, {csv_file}")
        except ImportError:
            logger.info(f"结果已保存: {json_file}")
    
    def print_summary(self, results: List[TestResult]):
        """打印测试摘要"""
        analysis = self.analyze_results(results)
        
        print("\n" + "="*60)
        print("📊 并发压力测试结果摘要")
        print("="*60)
        
        summary = analysis["summary"]
        print(f"📈 任务统计:")
        print(f"   总任务数: {summary['total_tasks']}")
        print(f"   成功任务: {summary['successful_tasks']}")
        print(f"   失败任务: {summary['failed_tasks']}")
        print(f"   成功率: {summary['success_rate']:.1f}%")
        
        perf = analysis["performance"]
        print(f"\n⏱️  性能统计:")
        print(f"   平均执行时间: {perf['execution_time']['mean']:.2f}s")
        print(f"   执行时间范围: {perf['execution_time']['min']:.2f}s - {perf['execution_time']['max']:.2f}s")
        print(f"   平均内存使用: {perf['memory_usage']['mean']:.1f}MB")
        print(f"   总提取帧数: {perf['keyframes_extracted']['total']}")
        
        if "system_performance" in analysis:
            sys_perf = analysis["system_performance"]
            print(f"\n💻 系统性能:")
            print(f"   平均CPU使用率: {sys_perf.get('avg_cpu_percent', 0):.1f}%")
            print(f"   平均内存使用率: {sys_perf.get('avg_memory_percent', 0):.1f}%")


class PerformanceMonitor:
    """系统性能监控器"""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.monitoring = False
        self.monitor_thread = None
        self.cpu_samples = []
        self.memory_samples = []
        self.disk_io_samples = []
        self.network_io_samples = []
    
    def start(self):
        """开始监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.cpu_samples = []
        self.memory_samples = []
        self.disk_io_samples = []
        self.network_io_samples = []
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("性能监控已启动")
    
    def stop(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        last_disk_io = psutil.disk_io_counters()
        last_net_io = psutil.net_io_counters()
        
        while self.monitoring:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=None)
                self.cpu_samples.append(cpu_percent)
                
                # 内存使用率
                memory = psutil.virtual_memory()
                self.memory_samples.append(memory.percent)
                
                # 磁盘IO
                current_disk_io = psutil.disk_io_counters()
                if last_disk_io:
                    disk_read_speed = (current_disk_io.read_bytes - last_disk_io.read_bytes) / self.interval
                    disk_write_speed = (current_disk_io.write_bytes - last_disk_io.write_bytes) / self.interval
                    self.disk_io_samples.append({
                        'read_speed': disk_read_speed,
                        'write_speed': disk_write_speed
                    })
                last_disk_io = current_disk_io
                
                # 网络IO
                current_net_io = psutil.net_io_counters()
                if last_net_io:
                    net_recv_speed = (current_net_io.bytes_recv - last_net_io.bytes_recv) / self.interval
                    net_sent_speed = (current_net_io.bytes_sent - last_net_io.bytes_sent) / self.interval
                    self.network_io_samples.append({
                        'recv_speed': net_recv_speed,
                        'sent_speed': net_sent_speed
                    })
                last_net_io = current_net_io
                
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"性能监控异常: {e}")
                break
    
    def get_stats(self) -> Dict:
        """获取统计数据"""
        stats = {}
        
        if self.cpu_samples:
            stats['avg_cpu_percent'] = statistics.mean(self.cpu_samples)
            stats['max_cpu_percent'] = max(self.cpu_samples)
            stats['min_cpu_percent'] = min(self.cpu_samples)
        
        if self.memory_samples:
            stats['avg_memory_percent'] = statistics.mean(self.memory_samples)
            stats['max_memory_percent'] = max(self.memory_samples)
            stats['min_memory_percent'] = min(self.memory_samples)
        
        if self.disk_io_samples:
            read_speeds = [s['read_speed'] for s in self.disk_io_samples]
            write_speeds = [s['write_speed'] for s in self.disk_io_samples]
            stats['avg_disk_read_speed'] = statistics.mean(read_speeds) / (1024*1024)  # MB/s
            stats['avg_disk_write_speed'] = statistics.mean(write_speeds) / (1024*1024)  # MB/s
        
        if self.network_io_samples:
            recv_speeds = [s['recv_speed'] for s in self.network_io_samples]
            sent_speeds = [s['sent_speed'] for s in self.network_io_samples]
            stats['avg_network_recv_speed'] = statistics.mean(recv_speeds) / (1024*1024)  # MB/s
            stats['avg_network_sent_speed'] = statistics.mean(sent_speeds) / (1024*1024)  # MB/s
        
        return stats


def main():
    """主函数"""
    print("🚀 Smart Keyframe Extractor - 并发压力测试工具")
    print("=" * 60)
    
    # 解析命令行参数（简化版）
    import argparse
    parser = argparse.ArgumentParser(description='并发压力测试工具')
    parser.add_argument('--video-dirs', nargs='+', default=['videos/'], 
                       help='视频文件目录列表')
    parser.add_argument('--max-workers', type=int, default=None,
                       help='最大并发数')
    parser.add_argument('--iterations', type=int, default=1,
                       help='测试迭代次数')
    parser.add_argument('--test-type', choices=['concurrent', 'sustained'], 
                       default='concurrent', help='测试类型')
    parser.add_argument('--duration', type=int, default=10,
                       help='持续测试时长(分钟)')
    parser.add_argument('--qps', type=float, default=1.0,
                       help='持续测试目标QPS')
    
    args = parser.parse_args()
    
    # 创建测试器
    tester = ConcurrentStressTester(max_workers=args.max_workers)
    
    # 定义测试配置
    test_configs = [
        {"name": "standard", "k": 5, "resolution": "original"},
        {"name": "fast", "k": 5, "resolution": "720p"},
        {"name": "ultra_fast", "k": 3, "resolution": "480p"},
    ]
    
    try:
        if args.test_type == 'concurrent':
            # 并发测试
            results = tester.run_concurrent_test(
                video_dirs=args.video_dirs,
                test_configs=test_configs,
                iterations=args.iterations
            )
        else:
            # 持续负载测试
            results = tester.run_sustained_load_test(
                video_dirs=args.video_dirs,
                test_config=test_configs[0],  # 使用第一个配置
                duration_minutes=args.duration,
                target_qps=args.qps
            )
        
        # 打印结果摘要
        tester.print_summary(results)
        
    except KeyboardInterrupt:
        logger.warning("测试被用户中断")
    except Exception as e:
        logger.error(f"测试发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
