#!/usr/bin/env python3
"""
智能性能监控和自动优化工具
基于实际测试数据提供动态性能优化建议
"""

import json
import csv
import os
import statistics
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self, results_dir: str = "wyze_auto_results"):
        self.results_dir = Path(results_dir)
        self.system_info = self._get_system_info()
        
    def _get_system_info(self) -> Dict:
        """获取系统信息"""
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'disk_free_gb': psutil.disk_usage('.').free / (1024**3),
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_test_results(self, test_file: str = None) -> Dict:
        """分析测试结果"""
        if test_file is None:
            # 找到最新的测试结果
            csv_files = list(self.results_dir.glob("concurrent_test_*.csv"))
            if not csv_files:
                raise FileNotFoundError("未找到测试结果文件")
            test_file = str(max(csv_files, key=os.path.getctime))
        
        # 读取CSV数据
        results = []
        with open(test_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['success'] == 'True':
                    results.append({
                        'execution_time': float(row['execution_time']),
                        'memory_usage': float(row['memory_usage']),
                        'video_size_mb': float(row['video_size_mb']),
                        'video_duration': float(row['video_duration']),
                        'fps_processed': float(row['fps_processed']),
                        'config': row['config']
                    })
        
        return self._calculate_metrics(results)
    
    def _calculate_metrics(self, results: List[Dict]) -> Dict:
        """计算性能指标"""
        if not results:
            return {}
        
        execution_times = [r['execution_time'] for r in results]
        memory_usage = [r['memory_usage'] for r in results]
        video_sizes = [r['video_size_mb'] for r in results]
        fps_rates = [r['fps_processed'] for r in results]
        
        # 按视频大小分组分析
        small_videos = [r for r in results if r['video_size_mb'] < 2.0]
        medium_videos = [r for r in results if 2.0 <= r['video_size_mb'] < 5.0]
        large_videos = [r for r in results if r['video_size_mb'] >= 5.0]
        
        return {
            'overall': {
                'total_tasks': len(results),
                'avg_execution_time': statistics.mean(execution_times),
                'median_execution_time': statistics.median(execution_times),
                'min_execution_time': min(execution_times),
                'max_execution_time': max(execution_times),
                'std_execution_time': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                'avg_memory_usage': statistics.mean(memory_usage),
                'avg_fps_processed': statistics.mean(fps_rates),
                'total_data_processed_gb': sum(video_sizes) / 1024
            },
            'by_size': {
                'small_videos': self._group_stats(small_videos),
                'medium_videos': self._group_stats(medium_videos), 
                'large_videos': self._group_stats(large_videos)
            },
            'efficiency_metrics': {
                'time_per_mb': statistics.mean([r['execution_time'] / max(r['video_size_mb'], 0.1) for r in results]),
                'memory_efficiency': statistics.mean([r['video_size_mb'] / max(r['memory_usage'], 1) for r in results]),
                'processing_efficiency': statistics.mean(fps_rates)
            }
        }
    
    def _group_stats(self, group: List[Dict]) -> Dict:
        """计算分组统计"""
        if not group:
            return {'count': 0}
        
        times = [r['execution_time'] for r in group]
        return {
            'count': len(group),
            'avg_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'avg_size_mb': statistics.mean([r['video_size_mb'] for r in group])
        }


class AutoOptimizer:
    """自动优化器"""
    
    def __init__(self, analyzer: PerformanceAnalyzer):
        self.analyzer = analyzer
        
    def recommend_optimal_config(self, target_performance: str = "balanced") -> Dict:
        """推荐最优配置"""
        metrics = self.analyzer.analyze_test_results()
        system_info = self.analyzer.system_info
        
        # 基于系统资源和性能目标推荐配置
        if target_performance == "speed":
            return self._speed_optimized_config(metrics, system_info)
        elif target_performance == "quality":
            return self._quality_optimized_config(metrics, system_info)
        else:  # balanced
            return self._balanced_config(metrics, system_info)
    
    def _speed_optimized_config(self, metrics: Dict, system_info: Dict) -> Dict:
        """速度优化配置"""
        cpu_count = system_info['cpu_count']
        memory_gb = system_info['memory_total_gb']
        
        return {
            'max_workers': min(cpu_count * 2, 16),
            'resolution': '480p',
            'k': 3,
            'batch_size': max(4, cpu_count),
            'expected_performance': {
                'avg_time_per_video': '5-10秒',
                'memory_usage': '低',
                'quality': '标准'
            },
            'reasoning': [
                f'基于{cpu_count}核CPU，使用{min(cpu_count * 2, 16)}并发',
                '480p分辨率平衡速度和质量',
                '3关键帧满足快速预览需求'
            ]
        }
    
    def _quality_optimized_config(self, metrics: Dict, system_info: Dict) -> Dict:
        """质量优化配置"""
        cpu_count = system_info['cpu_count']
        memory_gb = system_info['memory_total_gb']
        
        return {
            'max_workers': max(2, cpu_count // 2),
            'resolution': 'original',
            'k': 8,
            'batch_size': max(2, cpu_count // 2),
            'expected_performance': {
                'avg_time_per_video': '30-60秒',
                'memory_usage': '高',
                'quality': '最高'
            },
            'reasoning': [
                f'基于{cpu_count}核CPU，使用{max(2, cpu_count // 2)}并发避免资源竞争',
                '原始分辨率保证最高质量',
                '8关键帧提供详细分析'
            ]
        }
    
    def _balanced_config(self, metrics: Dict, system_info: Dict) -> Dict:
        """平衡配置"""
        cpu_count = system_info['cpu_count']
        memory_gb = system_info['memory_total_gb']
        
        # 根据历史性能调整
        if 'overall' in metrics:
            avg_time = metrics['overall']['avg_execution_time']
            if avg_time > 60:  # 如果平均时间过长，降低质量提升速度
                workers = min(cpu_count * 1.5, 12)
                resolution = '720p'
                k = 5
            elif avg_time < 10:  # 如果很快，可以提升质量
                workers = max(4, cpu_count)
                resolution = '1080p'
                k = 6
            else:  # 正常范围
                workers = cpu_count
                resolution = '720p'
                k = 5
        else:
            workers = cpu_count
            resolution = '720p'
            k = 5
        
        return {
            'max_workers': int(workers),
            'resolution': resolution,
            'k': k,
            'batch_size': max(4, cpu_count),
            'expected_performance': {
                'avg_time_per_video': '15-30秒',
                'memory_usage': '中等',
                'quality': '高'
            },
            'reasoning': [
                f'基于{cpu_count}核CPU和历史性能数据优化',
                f'{resolution}分辨率平衡质量和速度',
                f'{k}关键帧适合大多数应用场景'
            ]
        }
    
    def generate_optimization_report(self) -> str:
        """生成优化报告"""
        try:
            metrics = self.analyzer.analyze_test_results()
        except FileNotFoundError:
            return "❌ 未找到测试结果，请先运行压力测试"
        
        speed_config = self.recommend_optimal_config("speed")
        quality_config = self.recommend_optimal_config("quality")
        balanced_config = self.recommend_optimal_config("balanced")
        
        report = f"""
🎯 Smart Keyframe Extractor - 智能优化建议报告
{'='*60}

📊 当前性能分析
{'─'*30}
• 总任务数: {metrics['overall']['total_tasks']:,}
• 平均执行时间: {metrics['overall']['avg_execution_time']:.1f}秒
• 中位数执行时间: {metrics['overall']['median_execution_time']:.1f}秒
• 标准差: {metrics['overall']['std_execution_time']:.1f}秒
• 平均处理速度: {metrics['overall']['avg_fps_processed']:.1f} FPS
• 总处理数据: {metrics['overall']['total_data_processed_gb']:.2f} GB

📈 按视频大小分析
{'─'*30}
• 小文件 (<2MB): {metrics['by_size']['small_videos']['count']} 个, 平均 {metrics['by_size']['small_videos'].get('avg_time', 0):.1f}秒
• 中文件 (2-5MB): {metrics['by_size']['medium_videos']['count']} 个, 平均 {metrics['by_size']['medium_videos'].get('avg_time', 0):.1f}秒  
• 大文件 (>5MB): {metrics['by_size']['large_videos']['count']} 个, 平均 {metrics['by_size']['large_videos'].get('avg_time', 0):.1f}秒

🚀 推荐配置方案
{'─'*30}

🏃‍♂️ 速度优先配置
• 并发数: {speed_config['max_workers']}
• 分辨率: {speed_config['resolution']}
• 关键帧数: {speed_config['k']}
• 适用场景: 快速预览、实时处理
• 预期性能: {speed_config['expected_performance']['avg_time_per_video']}

🎨 质量优先配置  
• 并发数: {quality_config['max_workers']}
• 分辨率: {quality_config['resolution']}
• 关键帧数: {quality_config['k']}
• 适用场景: 详细分析、存档处理
• 预期性能: {quality_config['expected_performance']['avg_time_per_video']}

⚖️ 平衡配置 (推荐)
• 并发数: {balanced_config['max_workers']}
• 分辨率: {balanced_config['resolution']}
• 关键帧数: {balanced_config['k']}
• 适用场景: 日常使用、批量处理
• 预期性能: {balanced_config['expected_performance']['avg_time_per_video']}

💡 优化建议
{'─'*30}
"""
        
        # 基于数据生成具体建议
        if metrics['overall']['std_execution_time'] > 50:
            report += "• ⚠️ 执行时间波动较大，建议按文件大小分批处理\n"
        
        if metrics['overall']['avg_execution_time'] > 60:
            report += "• 🐌 平均执行时间较长，建议降低分辨率或减少关键帧数\n"
        
        if metrics['efficiency_metrics']['memory_efficiency'] < 1:
            report += "• 💾 内存使用效率偏低，建议优化内存管理\n"
        
        if metrics['overall']['avg_fps_processed'] < 20:
            report += "• 🔧 处理速度偏低，建议检查系统资源或升级硬件\n"
        
        report += f"""
🔍 下一步行动
{'─'*30}
1. 选择适合的配置运行新测试
2. 监控系统资源使用情况
3. 根据实际需求调整参数
4. 定期运行性能分析

📅 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='智能性能分析和优化工具')
    parser.add_argument('--results-dir', default='wyze_auto_results',
                       help='测试结果目录')
    parser.add_argument('--target', choices=['speed', 'quality', 'balanced'], 
                       default='balanced', help='优化目标')
    parser.add_argument('--report-only', action='store_true',
                       help='仅生成报告，不推荐配置')
    
    args = parser.parse_args()
    
    print("🔍 Smart Keyframe Extractor - 智能性能分析器")
    print("=" * 60)
    
    # 创建分析器
    analyzer = PerformanceAnalyzer(args.results_dir)
    optimizer = AutoOptimizer(analyzer)
    
    try:
        if args.report_only:
            # 仅生成分析报告
            print(optimizer.generate_optimization_report())
        else:
            # 生成优化建议
            config = optimizer.recommend_optimal_config(args.target)
            
            print(f"\n🎯 {args.target.upper()} 模式推荐配置:")
            print("-" * 30)
            print(f"并发数: {config['max_workers']}")
            print(f"分辨率: {config['resolution']}")
            print(f"关键帧数: {config['k']}")
            print(f"批处理大小: {config['batch_size']}")
            
            print(f"\n📈 预期性能:")
            for key, value in config['expected_performance'].items():
                print(f"  • {key}: {value}")
            
            print(f"\n💡 优化依据:")
            for reason in config['reasoning']:
                print(f"  • {reason}")
            
            # 生成完整报告
            print("\n" + "="*60)
            print("📊 完整性能分析报告")
            print("="*60)
            print(optimizer.generate_optimization_report())
    
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        print("请确保已运行压力测试并生成了结果文件")


if __name__ == "__main__":
    main()
