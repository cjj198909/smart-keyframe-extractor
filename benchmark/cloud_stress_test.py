#!/usr/bin/env python3
"""
云服务器压力测试启动脚本
适用于大规模并发测试和长时间稳定性测试
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.concurrent_stress_test import ConcurrentStressTester

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'stress_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_test_configs():
    """创建不同的测试配置"""
    return {
        "minimal": [
            {"name": "minimal_test", "k": 3, "resolution": "480p"}
        ],
        "standard": [
            {"name": "standard_low", "k": 5, "resolution": "720p"},
            {"name": "standard_high", "k": 5, "resolution": "original"}
        ],
        "comprehensive": [
            {"name": "ultra_fast", "k": 3, "resolution": "480p"},
            {"name": "fast", "k": 5, "resolution": "720p"},
            {"name": "balanced", "k": 5, "resolution": "720p"},
            {"name": "high_quality", "k": 10, "resolution": "original"},
            {"name": "max_quality", "k": 15, "resolution": "original"}
        ],
        "stress": [
            {"name": "stress_1", "k": 5, "resolution": "original"},
            {"name": "stress_2", "k": 10, "resolution": "original"},
            {"name": "stress_3", "k": 15, "resolution": "original"},
            {"name": "stress_4", "k": 20, "resolution": "original"}
        ]
    }


def run_cloud_stress_test():
    """运行云服务器压力测试"""
    parser = argparse.ArgumentParser(description='云服务器压力测试工具')
    
    # 基本参数
    parser.add_argument('--video-dirs', nargs='+', required=True,
                       help='视频文件目录列表 (必需)')
    parser.add_argument('--output-dir', default='cloud_stress_results',
                       help='结果输出目录')
    
    # 测试配置
    parser.add_argument('--test-profile', choices=['minimal', 'standard', 'comprehensive', 'stress'],
                       default='standard', help='测试配置档案')
    parser.add_argument('--custom-config', type=str,
                       help='自定义配置JSON文件路径')
    
    # 并发参数
    parser.add_argument('--max-workers', type=int, default=None,
                       help='最大并发数 (默认: CPU核心数+4)')
    parser.add_argument('--iterations', type=int, default=1,
                       help='每个配置的迭代次数')
    
    # 测试模式
    parser.add_argument('--test-mode', choices=['concurrent', 'sustained', 'both'],
                       default='concurrent', help='测试模式')
    
    # 持续测试参数
    parser.add_argument('--duration', type=int, default=30,
                       help='持续测试时长(分钟)')
    parser.add_argument('--target-qps', type=float, default=2.0,
                       help='持续测试目标QPS')
    
    # 高级选项
    parser.add_argument('--random-order', action='store_true', default=True,
                       help='随机打乱任务顺序')
    parser.add_argument('--video-extensions', nargs='+', 
                       default=['.mp4', '.avi', '.mov', '.mkv'],
                       help='支持的视频文件扩展名')
    parser.add_argument('--dry-run', action='store_true',
                       help='只显示测试计划不执行')
    
    args = parser.parse_args()
    
    # 验证视频目录
    valid_dirs = []
    for video_dir in args.video_dirs:
        if os.path.exists(video_dir):
            valid_dirs.append(video_dir)
            logger.info(f"✅ 视频目录有效: {video_dir}")
        else:
            logger.warning(f"⚠️ 视频目录不存在: {video_dir}")
    
    if not valid_dirs:
        logger.error("❌ 没有有效的视频目录")
        return
    
    # 获取测试配置
    if args.custom_config:
        with open(args.custom_config, 'r') as f:
            test_configs = json.load(f)
        logger.info(f"使用自定义配置: {args.custom_config}")
    else:
        all_configs = create_test_configs()
        test_configs = all_configs[args.test_profile]
        logger.info(f"使用预设配置: {args.test_profile}")
    
    # 创建测试器
    tester = ConcurrentStressTester(
        output_dir=args.output_dir,
        max_workers=args.max_workers
    )
    
    # 发现视频文件
    video_files = tester.discover_video_files(valid_dirs, args.video_extensions)
    
    if not video_files:
        logger.error("❌ 未发现任何视频文件")
        return
    
    # 计算测试规模
    total_tasks = len(video_files) * len(test_configs) * args.iterations
    logger.info(f"📊 测试规模预估:")
    logger.info(f"   视频文件: {len(video_files)}")
    logger.info(f"   配置方案: {len(test_configs)}")
    logger.info(f"   迭代次数: {args.iterations}")
    logger.info(f"   总任务数: {total_tasks}")
    logger.info(f"   最大并发: {tester.max_workers}")
    
    if args.dry_run:
        logger.info("🔍 干跑模式 - 仅显示测试计划")
        for i, config in enumerate(test_configs):
            logger.info(f"   配置 {i+1}: {config}")
        return
    
    # 确认开始测试
    logger.info("\n🚀 准备开始压力测试...")
    logger.info(f"测试将在 5 秒后开始...")
    
    import time
    for i in range(5, 0, -1):
        logger.info(f"倒计时: {i}")
        time.sleep(1)
    
    try:
        results_all = []
        
        # 并发测试
        if args.test_mode in ['concurrent', 'both']:
            logger.info("🔥 开始并发压力测试...")
            concurrent_results = tester.run_concurrent_test(
                video_dirs=valid_dirs,
                test_configs=test_configs,
                iterations=args.iterations,
                random_order=args.random_order
            )
            results_all.extend(concurrent_results)
            
            # 打印并发测试摘要
            logger.info("\n" + "="*50)
            logger.info("📊 并发测试结果:")
            tester.print_summary(concurrent_results)
        
        # 持续负载测试
        if args.test_mode in ['sustained', 'both']:
            logger.info(f"\n🔥 开始持续负载测试 ({args.duration}分钟)...")
            sustained_results = tester.run_sustained_load_test(
                video_dirs=valid_dirs,
                test_config=test_configs[0],  # 使用第一个配置
                duration_minutes=args.duration,
                target_qps=args.target_qps
            )
            results_all.extend(sustained_results)
            
            # 打印持续测试摘要
            logger.info("\n" + "="*50)
            logger.info("📊 持续负载测试结果:")
            tester.print_summary(sustained_results)
        
        # 总结
        if results_all:
            logger.info("\n" + "="*60)
            logger.info("🎉 所有测试完成")
            logger.info("="*60)
            tester.print_summary(results_all)
            
            # 保存汇总报告
            summary_file = Path(args.output_dir) / f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            analysis = tester.analyze_results(results_all)
            analysis['test_parameters'] = {
                'video_dirs': valid_dirs,
                'test_profile': args.test_profile,
                'test_mode': args.test_mode,
                'max_workers': tester.max_workers,
                'iterations': args.iterations,
                'total_videos': len(video_files),
                'total_configs': len(test_configs),
                'total_tasks': len(results_all)
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 汇总报告已保存: {summary_file}")
        
    except KeyboardInterrupt:
        logger.warning("⏹️ 测试被用户中断")
    except Exception as e:
        logger.error(f"❌ 测试发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_cloud_stress_test()
