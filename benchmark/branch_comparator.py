#!/usr/bin/env python3
"""
分支性能对比工具
比较不同代码分支的性能差异，用于优化验证
"""

import json
import subprocess
import time
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))


class BranchComparator:
    """分支性能对比器"""
    
    def __init__(self, base_branch: str = "main", compare_branch: str = None):
        self.base_branch = base_branch
        self.compare_branch = compare_branch
        self.results_dir = Path("branch_comparison_results")
        self.results_dir.mkdir(exist_ok=True)
        
    def run_branch_comparison(self, test_video: str = "videos/785023.mp4", 
                            iterations: int = 5) -> Dict:
        """运行分支对比测试"""
        print("🔀 分支性能对比测试")
        print("=" * 50)
        
        results = {
            'test_info': {
                'base_branch': self.base_branch,
                'compare_branch': self.compare_branch,
                'test_video': test_video,
                'iterations': iterations,
                'timestamp': datetime.now().isoformat()
            },
            'results': {}
        }
        
        # 获取当前分支
        current_branch = self._get_current_branch()
        
        try:
            # 测试基准分支
            print(f"\n📍 切换到基准分支: {self.base_branch}")
            self._checkout_branch(self.base_branch)
            base_results = self._run_performance_test(test_video, iterations, f"{self.base_branch}_branch")
            results['results'][self.base_branch] = base_results
            
            # 测试对比分支 (如果指定)
            if self.compare_branch:
                print(f"\n📍 切换到对比分支: {self.compare_branch}")
                self._checkout_branch(self.compare_branch)
                compare_results = self._run_performance_test(test_video, iterations, f"{self.compare_branch}_branch")
                results['results'][self.compare_branch] = compare_results
                
                # 生成对比分析
                results['comparison'] = self._analyze_differences(base_results, compare_results)
        
        finally:
            # 恢复原始分支
            print(f"\n↩️ 恢复到原始分支: {current_branch}")
            self._checkout_branch(current_branch)
        
        # 保存结果
        results_file = self.results_dir / f"branch_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 结果已保存到: {results_file}")
        return results
    
    def _get_current_branch(self) -> str:
        """获取当前Git分支"""
        try:
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"
    
    def _checkout_branch(self, branch: str):
        """切换Git分支"""
        try:
            subprocess.run(['git', 'checkout', branch], 
                          capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ 分支切换失败: {e}")
            print("请确保分支存在且工作目录干净")
    
    def _run_performance_test(self, test_video: str, iterations: int, branch_name: str) -> Dict:
        """运行性能测试"""
        print(f"\n🏃‍♂️ 执行性能测试 ({branch_name})...")
        
        # 确保模块重新导入
        if 'smart_keyframe_extractor.extractor' in sys.modules:
            del sys.modules['smart_keyframe_extractor.extractor']
        
        from smart_keyframe_extractor.extractor import extract_top_k_keyframes
        
        results = {
            'branch': branch_name,
            'iterations': [],
            'summary': {}
        }
        
        for i in range(iterations):
            print(f"  📊 迭代 {i+1}/{iterations}")
            
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            try:
                result = extract_top_k_keyframes(
                    video_path=test_video,
                    k=5,
                    resolution="720p",
                    return_base64=False,
                    save_files=False
                )
                
                end_time = time.time()
                end_memory = self._get_memory_usage()
                
                iteration_result = {
                    'iteration': i + 1,
                    'success': True,
                    'execution_time': end_time - start_time,
                    'memory_delta': end_memory - start_memory,
                    'frames_extracted': len(result.get('frames', [])),
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                iteration_result = {
                    'iteration': i + 1,
                    'success': False,
                    'error': str(e),
                    'execution_time': 0,
                    'memory_delta': 0,
                    'frames_extracted': 0,
                    'timestamp': datetime.now().isoformat()
                }
            
            results['iterations'].append(iteration_result)
            
            # 短暂休息避免系统负载影响
            time.sleep(1)
        
        # 计算汇总统计
        successful_iterations = [r for r in results['iterations'] if r['success']]
        if successful_iterations:
            execution_times = [r['execution_time'] for r in successful_iterations]
            memory_deltas = [r['memory_delta'] for r in successful_iterations]
            
            results['summary'] = {
                'success_rate': len(successful_iterations) / iterations,
                'avg_execution_time': sum(execution_times) / len(execution_times),
                'min_execution_time': min(execution_times),
                'max_execution_time': max(execution_times),
                'avg_memory_delta': sum(memory_deltas) / len(memory_deltas),
                'total_frames': sum(r['frames_extracted'] for r in successful_iterations)
            }
        
        return results
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用量 (MB)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
    
    def _analyze_differences(self, base_results: Dict, compare_results: Dict) -> Dict:
        """分析两个分支的性能差异"""
        base_summary = base_results.get('summary', {})
        compare_summary = compare_results.get('summary', {})
        
        if not base_summary or not compare_summary:
            return {'error': '无法比较：某个分支测试失败'}
        
        # 计算性能改进百分比
        def calculate_improvement(base_val: float, compare_val: float) -> float:
            if base_val == 0:
                return 0
            return ((base_val - compare_val) / base_val) * 100
        
        analysis = {
            'execution_time': {
                'base_avg': base_summary['avg_execution_time'],
                'compare_avg': compare_summary['avg_execution_time'],
                'improvement_percent': calculate_improvement(
                    base_summary['avg_execution_time'], 
                    compare_summary['avg_execution_time']
                ),
                'faster': compare_summary['avg_execution_time'] < base_summary['avg_execution_time']
            },
            'memory_usage': {
                'base_avg': base_summary['avg_memory_delta'],
                'compare_avg': compare_summary['avg_memory_delta'],
                'improvement_percent': calculate_improvement(
                    base_summary['avg_memory_delta'], 
                    compare_summary['avg_memory_delta']
                ),
                'more_efficient': compare_summary['avg_memory_delta'] < base_summary['avg_memory_delta']
            },
            'stability': {
                'base_success_rate': base_summary['success_rate'],
                'compare_success_rate': compare_summary['success_rate'],
                'more_stable': compare_summary['success_rate'] >= base_summary['success_rate']
            }
        }
        
        # 总体评估
        improvements = []
        regressions = []
        
        if analysis['execution_time']['faster']:
            improvements.append(f"执行时间提升 {analysis['execution_time']['improvement_percent']:.1f}%")
        else:
            regressions.append(f"执行时间降低 {-analysis['execution_time']['improvement_percent']:.1f}%")
        
        if analysis['memory_usage']['more_efficient']:
            improvements.append(f"内存效率提升 {analysis['memory_usage']['improvement_percent']:.1f}%")
        else:
            regressions.append(f"内存使用增加 {-analysis['memory_usage']['improvement_percent']:.1f}%")
        
        if analysis['stability']['more_stable']:
            improvements.append("稳定性保持或提升")
        else:
            regressions.append("稳定性下降")
        
        analysis['overall_assessment'] = {
            'improvements': improvements,
            'regressions': regressions,
            'recommendation': self._generate_recommendation(improvements, regressions)
        }
        
        return analysis
    
    def _generate_recommendation(self, improvements: List[str], regressions: List[str]) -> str:
        """生成推荐建议"""
        if len(improvements) > len(regressions):
            return "✅ 推荐合并：性能改进明显"
        elif len(regressions) > len(improvements):
            return "❌ 不推荐合并：存在性能倒退"
        else:
            return "⚖️ 需要权衡：性能改进和倒退并存"
    
    def print_comparison_report(self, results: Dict):
        """打印对比报告"""
        print("\n" + "="*60)
        print("📊 分支性能对比报告")
        print("="*60)
        
        test_info = results.get('test_info', {})
        print(f"📅 测试时间: {test_info.get('timestamp', 'Unknown')}")
        print(f"🎯 测试视频: {test_info.get('test_video', 'Unknown')}")
        print(f"🔄 迭代次数: {test_info.get('iterations', 'Unknown')}")
        
        # 显示各分支结果
        for branch, result in results.get('results', {}).items():
            summary = result.get('summary', {})
            if summary:
                print(f"\n📍 {branch} 分支:")
                print(f"  ✅ 成功率: {summary['success_rate']*100:.1f}%")
                print(f"  ⏱️ 平均执行时间: {summary['avg_execution_time']:.2f}秒")
                print(f"  💾 平均内存增长: {summary['avg_memory_delta']:.1f}MB")
                print(f"  📊 总提取帧数: {summary['total_frames']}")
        
        # 显示对比分析
        comparison = results.get('comparison')
        if comparison and 'error' not in comparison:
            print(f"\n🔍 性能对比分析:")
            print("-" * 30)
            
            exec_analysis = comparison['execution_time']
            if exec_analysis['faster']:
                print(f"⚡ 执行速度: 提升 {exec_analysis['improvement_percent']:.1f}%")
            else:
                print(f"🐌 执行速度: 下降 {-exec_analysis['improvement_percent']:.1f}%")
            
            mem_analysis = comparison['memory_usage']
            if mem_analysis['more_efficient']:
                print(f"💾 内存效率: 提升 {mem_analysis['improvement_percent']:.1f}%")
            else:
                print(f"💾 内存使用: 增加 {-mem_analysis['improvement_percent']:.1f}%")
            
            assessment = comparison['overall_assessment']
            print(f"\n{assessment['recommendation']}")
            
            if assessment['improvements']:
                print("\n✅ 改进点:")
                for imp in assessment['improvements']:
                    print(f"  • {imp}")
            
            if assessment['regressions']:
                print("\n❌ 倒退点:")
                for reg in assessment['regressions']:
                    print(f"  • {reg}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='分支性能对比工具')
    parser.add_argument('--base-branch', default='main', help='基准分支')
    parser.add_argument('--compare-branch', help='对比分支')
    parser.add_argument('--test-video', default='videos/785023.mp4', help='测试视频')
    parser.add_argument('--iterations', type=int, default=5, help='测试迭代次数')
    parser.add_argument('--list-branches', action='store_true', help='列出可用分支')
    
    args = parser.parse_args()
    
    if args.list_branches:
        try:
            result = subprocess.run(['git', 'branch', '-a'], 
                                  capture_output=True, text=True, check=True)
            print("📋 可用分支:")
            print(result.stdout)
        except subprocess.CalledProcessError:
            print("❌ 无法获取分支列表，请确保在Git仓库中")
        return
    
    if not args.compare_branch:
        print("❌ 请指定要对比的分支 (--compare-branch)")
        print("💡 使用 --list-branches 查看可用分支")
        return
    
    if not os.path.exists(args.test_video):
        print(f"❌ 测试视频不存在: {args.test_video}")
        return
    
    comparator = BranchComparator(args.base_branch, args.compare_branch)
    
    try:
        results = comparator.run_branch_comparison(args.test_video, args.iterations)
        comparator.print_comparison_report(results)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    main()
