#!/usr/bin/env python3
"""
大规模视频数据集压力测试
Large Dataset Stress Testing

专门针对大规模视频数据集的压力测试工具
"""

import os
import sys
import argparse
import time
import json
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from smart_keyframe_extractor.extractor import extract_top_k_keyframes

class LargeDatasetStressTester:
    """大规模数据集压力测试器"""
    
    def __init__(self, video_dirs: List[str], output_dir: str = "test_auto_results"):
        self.video_dirs = video_dirs
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def discover_videos(self) -> List[Path]:
        """发现所有视频文件"""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
        video_files = []
        
        for video_dir in self.video_dirs:
            video_path = Path(video_dir)
            if not video_path.exists():
                self.logger.warning(f"目录不存在: {video_dir}")
                continue
                
            for file_path in video_path.rglob('*'):
                if file_path.suffix.lower() in video_extensions:
                    video_files.append(file_path)
        
        self.logger.info(f"发现 {len(video_files)} 个视频文件")
        return sorted(video_files)
    
    def process_single_video(self, video_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个视频"""
        start_time = time.time()
        
        try:
            # 提取关键帧
            result = extract_top_k_keyframes(
                str(video_path),
                k=config.get('k', 3),
                save_files=False,  # 不保存文件，仅测试性能
                resolution=config.get('resolution', '720p')
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            return {
                'video_path': str(video_path),
                'video_name': video_path.name,
                'status': 'success',
                'processing_time': processing_time,
                'keyframes_count': len(result['keyframes']),
                'config': config,
                'file_size_mb': video_path.stat().st_size / (1024 * 1024),
                'error': None
            }
            
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            
            return {
                'video_path': str(video_path),
                'video_name': video_path.name,
                'status': 'failed',
                'processing_time': processing_time,
                'keyframes_count': 0,
                'config': config,
                'file_size_mb': video_path.stat().st_size / (1024 * 1024) if video_path.exists() else 0,
                'error': str(e)
            }
    
    def run_concurrent_test(self, video_files: List[Path], max_workers: int = 4) -> List[Dict[str, Any]]:
        """运行并发测试"""
        test_config = {
            'k': 3,
            'resolution': '720p'
        }
        
        results = []
        
        self.logger.info(f"开始并发测试，最大worker数: {max_workers}")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_video = {
                executor.submit(self.process_single_video, video_file, test_config): video_file 
                for video_file in video_files
            }
            
            # 收集结果
            for i, future in enumerate(as_completed(future_to_video), 1):
                video_file = future_to_video[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    status_icon = "✅" if result['status'] == 'success' else "❌"
                    self.logger.info(
                        f"{status_icon} [{i}/{len(video_files)}] {video_file.name} - "
                        f"{result['processing_time']:.2f}s"
                    )
                    
                except Exception as e:
                    self.logger.error(f"处理 {video_file.name} 时出错: {e}")
                    results.append({
                        'video_path': str(video_file),
                        'video_name': video_file.name,
                        'status': 'error',
                        'processing_time': 0,
                        'keyframes_count': 0,
                        'config': test_config,
                        'file_size_mb': 0,
                        'error': str(e)
                    })
        
        return results
    
    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析测试结果"""
        total_videos = len(results)
        successful_videos = sum(1 for r in results if r['status'] == 'success')
        failed_videos = total_videos - successful_videos
        
        if successful_videos > 0:
            successful_results = [r for r in results if r['status'] == 'success']
            total_processing_time = sum(r['processing_time'] for r in successful_results)
            avg_processing_time = total_processing_time / successful_videos
            total_file_size = sum(r['file_size_mb'] for r in successful_results)
            avg_file_size = total_file_size / successful_videos
            processing_speed = total_file_size / total_processing_time if total_processing_time > 0 else 0
        else:
            avg_processing_time = 0
            avg_file_size = 0
            processing_speed = 0
            total_processing_time = 0
        
        analysis = {
            'test_summary': {
                'total_videos': total_videos,
                'successful_videos': successful_videos,
                'failed_videos': failed_videos,
                'success_rate': (successful_videos / total_videos * 100) if total_videos > 0 else 0
            },
            'performance_metrics': {
                'total_processing_time': total_processing_time,
                'avg_processing_time': avg_processing_time,
                'avg_file_size_mb': avg_file_size,
                'processing_speed_mb_per_sec': processing_speed
            },
            'detailed_results': results
        }
        
        return analysis
    
    def save_results(self, analysis: Dict[str, Any], test_name: str = None):
        """保存测试结果"""
        if test_name is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            test_name = f"large_dataset_test_{timestamp}"
        
        # 保存JSON格式
        json_file = self.output_dir / f"{test_name}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        # 保存CSV格式
        csv_file = self.output_dir / f"{test_name}.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("video_name,status,processing_time,keyframes_count,file_size_mb,error\n")
            for result in analysis['detailed_results']:
                f.write(f"{result['video_name']},{result['status']},{result['processing_time']:.2f},"
                       f"{result['keyframes_count']},{result['file_size_mb']:.2f},\"{result['error'] or ''}\"\n")
        
        self.logger.info(f"结果已保存到: {json_file} 和 {csv_file}")
    
    def print_summary(self, analysis: Dict[str, Any]):
        """打印测试摘要"""
        summary = analysis['test_summary']
        metrics = analysis['performance_metrics']
        
        print("\n" + "="*60)
        print("🎬 大规模视频数据集压力测试结果")
        print("="*60)
        
        print(f"\n📊 测试概览:")
        print(f"  总视频数: {summary['total_videos']}")
        print(f"  成功处理: {summary['successful_videos']}")
        print(f"  失败数量: {summary['failed_videos']}")
        print(f"  成功率: {summary['success_rate']:.1f}%")
        
        if summary['successful_videos'] > 0:
            print(f"\n⚡ 性能指标:")
            print(f"  总处理时间: {metrics['total_processing_time']:.1f} 秒")
            print(f"  平均处理时间: {metrics['avg_processing_time']:.2f} 秒/视频")
            print(f"  平均文件大小: {metrics['avg_file_size_mb']:.2f} MB")
            print(f"  处理速度: {metrics['processing_speed_mb_per_sec']:.2f} MB/秒")
        
        # 显示失败的视频
        failed_results = [r for r in analysis['detailed_results'] if r['status'] != 'success']
        if failed_results:
            print(f"\n❌ 失败的视频:")
            for result in failed_results[:5]:  # 只显示前5个
                print(f"  - {result['video_name']}: {result['error']}")
            if len(failed_results) > 5:
                print(f"  ... 还有 {len(failed_results) - 5} 个失败的视频")

def setup_test_environment():
    """设置测试环境"""
    test_dirs = [
        "videos",  # 项目内的测试视频
        "/tmp/test_videos"  # 可选的外部测试目录
    ]
    
    # 过滤存在的目录
    existing_dirs = [d for d in test_dirs if Path(d).exists()]
    
    print("🎬 大规模视频数据集压力测试")
    print("="*50)
    
    if not existing_dirs:
        print("⚠️  未找到测试视频目录")
        print("请将测试视频放在以下目录之一:")
        for d in test_dirs:
            print(f"  - {d}")
        return []
    
    return existing_dirs

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='大规模视频数据集压力测试')
    parser.add_argument('--video-dirs', nargs='+', 
                       help='视频目录路径列表')
    parser.add_argument('--max-workers', type=int, default=4,
                       help='最大并发worker数 (默认: 4)')
    parser.add_argument('--output-dir', default='test_auto_results',
                       help='结果输出目录 (默认: test_auto_results)')
    
    args = parser.parse_args()
    
    # 确定视频目录
    if args.video_dirs:
        video_dirs = args.video_dirs
    else:
        video_dirs = setup_test_environment()
        if not video_dirs:
            return
    
    # 运行测试
    tester = LargeDatasetStressTester(video_dirs, args.output_dir)
    
    # 发现视频文件
    video_files = tester.discover_videos()
    if not video_files:
        print("❌ 未发现任何视频文件")
        return
    
    # 运行测试
    print(f"\n🚀 开始测试 {len(video_files)} 个视频文件...")
    start_time = time.time()
    
    results = tester.run_concurrent_test(video_files, args.max_workers)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # 分析结果
    analysis = tester.analyze_results(results)
    analysis['test_info'] = {
        'total_test_time': total_time,
        'max_workers': args.max_workers,
        'video_directories': video_dirs
    }
    
    # 保存和显示结果
    tester.save_results(analysis)
    tester.print_summary(analysis)
    
    print(f"\n⏱️  总测试时间: {total_time:.1f} 秒")
    print(f"📁 结果保存在: {args.output_dir}/")

if __name__ == "__main__":
    main()
