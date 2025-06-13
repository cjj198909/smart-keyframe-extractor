#!/usr/bin/env python3
"""
智能批处理优化器
基于文件大小和复杂度智能分批处理，提升整体性能
"""

import os
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from smart_keyframe_extractor.extractor import extract_top_k_keyframes


class IntelligentBatchProcessor:
    """智能批处理器"""
    
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.results = []
        
    def analyze_video_complexity(self, video_path: str) -> Dict:
        """分析视频复杂度"""
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return {'complexity': 'unknown', 'size_mb': 0, 'duration': 0}
            
            # 获取基本信息
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            cap.release()
            
            # 文件大小
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            
            # 复杂度评估
            pixel_count = width * height
            complexity_score = (pixel_count * duration) / 1000000
            
            if complexity_score < 50:
                complexity = 'simple'
            elif complexity_score < 200:
                complexity = 'medium'
            else:
                complexity = 'complex'
            
            return {
                'complexity': complexity,
                'size_mb': file_size,
                'duration': duration,
                'resolution': f"{width}x{height}",
                'total_frames': total_frames,
                'fps': fps,
                'complexity_score': complexity_score
            }
            
        except Exception as e:
            print(f"⚠️ 分析视频复杂度失败: {e}")
            file_size = os.path.getsize(video_path) / (1024 * 1024) if os.path.exists(video_path) else 0
            return {
                'complexity': 'unknown',
                'size_mb': file_size,
                'duration': 0,
                'error': str(e)
            }
    
    def create_optimal_batches(self, video_files: List[str]) -> List[List[Dict]]:
        """创建最优批次"""
        print("🔍 分析视频复杂度...")
        
        # 分析所有视频
        video_info = []
        for i, video_path in enumerate(video_files):
            print(f"  分析 {i+1}/{len(video_files)}: {Path(video_path).name}")
            info = self.analyze_video_complexity(video_path)
            info['path'] = video_path
            video_info.append(info)
        
        # 按复杂度和大小分组
        simple_videos = [v for v in video_info if v['complexity'] == 'simple']
        medium_videos = [v for v in video_info if v['complexity'] == 'medium']
        complex_videos = [v for v in video_info if v['complexity'] == 'complex']
        unknown_videos = [v for v in video_info if v['complexity'] == 'unknown']
        
        print(f"\n📊 视频分类结果:")
        print(f"  🟢 简单视频: {len(simple_videos)} 个")
        print(f"  🟡 中等视频: {len(medium_videos)} 个")
        print(f"  🔴 复杂视频: {len(complex_videos)} 个")
        print(f"  ⚪ 未知视频: {len(unknown_videos)} 个")
        
        # 创建批次
        batches = []
        
        # 简单视频 - 大批次并发
        if simple_videos:
            batch_size = min(16, len(simple_videos))
            for i in range(0, len(simple_videos), batch_size):
                batch = simple_videos[i:i + batch_size]
                batches.append({
                    'videos': batch,
                    'type': 'simple',
                    'recommended_workers': min(self.max_workers, len(batch)),
                    'config': {'k': 3, 'resolution': '480p'}
                })
        
        # 中等视频 - 中等批次
        if medium_videos:
            batch_size = min(8, len(medium_videos))
            for i in range(0, len(medium_videos), batch_size):
                batch = medium_videos[i:i + batch_size]
                batches.append({
                    'videos': batch,
                    'type': 'medium',
                    'recommended_workers': min(self.max_workers // 2, len(batch)),
                    'config': {'k': 5, 'resolution': '720p'}
                })
        
        # 复杂视频 - 小批次串行
        if complex_videos:
            batch_size = min(4, len(complex_videos))
            for i in range(0, len(complex_videos), batch_size):
                batch = complex_videos[i:i + batch_size]
                batches.append({
                    'videos': batch,
                    'type': 'complex',
                    'recommended_workers': min(2, len(batch)),
                    'config': {'k': 5, 'resolution': '720p'}
                })
        
        # 未知视频 - 保守处理
        if unknown_videos:
            for video in unknown_videos:
                batches.append({
                    'videos': [video],
                    'type': 'unknown',
                    'recommended_workers': 1,
                    'config': {'k': 3, 'resolution': '480p'}
                })
        
        return batches
    
    def process_single_video(self, video_info: Dict, config: Dict) -> Dict:
        """处理单个视频"""
        video_path = video_info['path']
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
            
            return {
                'video_path': video_path,
                'video_info': video_info,
                'config': config,
                'success': True,
                'execution_time': execution_time,
                'frames_extracted': len(result.get('frames', [])),
                'result': result
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'video_path': video_path,
                'video_info': video_info,
                'config': config,
                'success': False,
                'execution_time': execution_time,
                'error': str(e)
            }
    
    def process_batch(self, batch: Dict) -> List[Dict]:
        """处理一个批次"""
        videos = batch['videos']
        workers = batch['recommended_workers']
        config = batch['config']
        batch_type = batch['type']
        
        print(f"\n🚀 处理 {batch_type} 批次: {len(videos)} 个视频, {workers} 并发")
        
        batch_results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # 提交任务
            futures = {
                executor.submit(self.process_single_video, video, config): video
                for video in videos
            }
            
            # 收集结果
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                batch_results.append(result)
                completed += 1
                
                status = "✅" if result['success'] else "❌"
                video_name = Path(result['video_path']).name
                print(f"  {status} {completed}/{len(videos)}: {video_name} ({result['execution_time']:.1f}s)")
        
        batch_time = time.time() - start_time
        success_count = sum(1 for r in batch_results if r['success'])
        
        print(f"📊 批次完成: {success_count}/{len(videos)} 成功, 总时间 {batch_time:.1f}s")
        
        return batch_results
    
    def process_videos_intelligently(self, video_files: List[str]) -> Dict:
        """智能处理视频列表"""
        print(f"🎯 智能批处理开始: {len(video_files)} 个视频")
        print("=" * 60)
        
        # 创建最优批次
        batches = self.create_optimal_batches(video_files)
        
        # 处理所有批次
        all_results = []
        total_start_time = time.time()
        
        for i, batch in enumerate(batches):
            print(f"\n📦 批次 {i+1}/{len(batches)}")
            batch_results = self.process_batch(batch)
            all_results.extend(batch_results)
            
            # 批次间短暂休息
            if i < len(batches) - 1:
                print("⏸️ 批次间休息 2秒...")
                time.sleep(2)
        
        total_time = time.time() - total_start_time
        
        # 汇总统计
        successful_results = [r for r in all_results if r['success']]
        failed_results = [r for r in all_results if not r['success']]
        
        summary = {
            'total_videos': len(video_files),
            'total_batches': len(batches),
            'successful_videos': len(successful_results),
            'failed_videos': len(failed_results),
            'success_rate': len(successful_results) / len(video_files) * 100,
            'total_execution_time': total_time,
            'avg_time_per_video': total_time / len(video_files),
            'total_frames_extracted': sum(r.get('frames_extracted', 0) for r in successful_results)
        }
        
        return {
            'summary': summary,
            'results': all_results,
            'batches_info': [
                {
                    'type': batch['type'],
                    'video_count': len(batch['videos']),
                    'workers': batch['recommended_workers'],
                    'config': batch['config']
                }
                for batch in batches
            ]
        }
    
    def print_final_report(self, processing_result: Dict):
        """打印最终报告"""
        summary = processing_result['summary']
        
        print(f"\n🎉 智能批处理完成报告")
        print("=" * 60)
        print(f"📊 总体统计:")
        print(f"  • 总视频数: {summary['total_videos']}")
        print(f"  • 批次数: {summary['total_batches']}")
        print(f"  • 成功处理: {summary['successful_videos']}")
        print(f"  • 失败处理: {summary['failed_videos']}")
        print(f"  • 成功率: {summary['success_rate']:.1f}%")
        print(f"  • 总执行时间: {summary['total_execution_time']:.1f}秒")
        print(f"  • 平均时间/视频: {summary['avg_time_per_video']:.1f}秒")
        print(f"  • 总提取帧数: {summary['total_frames_extracted']}")
        
        print(f"\n📦 批次信息:")
        for i, batch_info in enumerate(processing_result['batches_info']):
            print(f"  批次 {i+1}: {batch_info['type']} ({batch_info['video_count']} 视频, "
                  f"{batch_info['workers']} 并发, {batch_info['config']})")
        
        # 性能对比
        if summary['avg_time_per_video'] < 20:
            print(f"\n✅ 性能评估: 优秀 (平均 {summary['avg_time_per_video']:.1f}s/视频)")
        elif summary['avg_time_per_video'] < 40:
            print(f"\n🟡 性能评估: 良好 (平均 {summary['avg_time_per_video']:.1f}s/视频)")
        else:
            print(f"\n🔴 性能评估: 需要优化 (平均 {summary['avg_time_per_video']:.1f}s/视频)")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='智能批处理优化器')
    parser.add_argument('--video-dir', required=True, help='视频目录路径')
    parser.add_argument('--max-workers', type=int, default=8, help='最大工作线程数')
    parser.add_argument('--output-file', help='结果输出文件')
    parser.add_argument('--dry-run', action='store_true', help='仅分析不处理')
    
    args = parser.parse_args()
    
    # 收集视频文件
    video_dir = Path(args.video_dir)
    if not video_dir.exists():
        print(f"❌ 视频目录不存在: {video_dir}")
        return
    
    video_files = []
    for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv']:
        video_files.extend(video_dir.glob(ext))
        video_files.extend(video_dir.glob(ext.upper()))
    
    video_files = [str(f) for f in video_files]
    
    if not video_files:
        print(f"❌ 在 {video_dir} 中未找到视频文件")
        return
    
    print(f"📁 发现 {len(video_files)} 个视频文件")
    
    # 创建处理器
    processor = IntelligentBatchProcessor(max_workers=args.max_workers)
    
    if args.dry_run:
        print("🔍 仅分析模式，不进行实际处理...")
        batches = processor.create_optimal_batches(video_files)
        
        print(f"\n📊 批次分析结果:")
        for i, batch in enumerate(batches):
            print(f"  批次 {i+1}: {batch['type']} ({len(batch['videos'])} 视频, "
                  f"{batch['recommended_workers']} 并发)")
        
        total_estimated_time = sum(
            len(batch['videos']) * (10 if batch['type'] == 'simple' 
                                  else 25 if batch['type'] == 'medium' 
                                  else 45) / batch['recommended_workers']
            for batch in batches
        )
        print(f"\n⏱️ 预估总处理时间: {total_estimated_time:.0f} 秒")
        
    else:
        # 执行智能处理
        result = processor.process_videos_intelligently(video_files)
        processor.print_final_report(result)
        
        # 保存结果
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 结果已保存到: {args.output_file}")


if __name__ == "__main__":
    main()
