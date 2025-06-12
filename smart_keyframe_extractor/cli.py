#!/usr/bin/env python3
"""
命令行接口
"""

import sys
import argparse
import logging
from smart_keyframe_extractor.extractor import extract_top_k_keyframes

logger = logging.getLogger(__name__)


def main():
    """命令行主入口"""
    parser = argparse.ArgumentParser(
        description='智能视频关键帧提取工具（支持自适应模式、分辨率选择和base64输出）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 固定提取5帧，720p分辨率，输出base64
  smart-keyframe video.mp4 -k 5 --resolution 720p --base64
  
  # 自适应模式，480p分辨率，同时保存文件和base64
  smart-keyframe video.mp4 -o output_frames -k auto --resolution 480p --base64 --save-files
  
  # 每10秒提取1帧，原始分辨率，仅输出base64
  smart-keyframe video.mp4 --mode interval --interval 10 --frames-per-interval 1 --base64
  
  # 每5秒提取2帧，最少3帧，最多20帧，360p分辨率，保存文件
  smart-keyframe video.mp4 -o output_frames --mode interval --interval 5 --frames-per-interval 2 --min-frames 3 --max-frames 20 --resolution 360p --save-files
        """
    )
    
    parser.add_argument('input', help='视频文件路径')
    parser.add_argument('-o', '--output', help='输出目录（当--save-files时必需）')
    parser.add_argument('-k', '--keyframes', default='5',
                       help='要提取的关键帧数量，可以是数字或 "auto"')
    parser.add_argument('--mode', choices=['fixed', 'adaptive', 'interval'],
                       help='自适应模式')
    parser.add_argument('--interval', type=float, default=10.0,
                       help='时间间隔（秒），用于 interval 模式')
    parser.add_argument('--frames-per-interval', type=int, default=1,
                       help='每个时间间隔提取的帧数')
    parser.add_argument('--min-frames', type=int, default=3,
                       help='最小帧数')
    parser.add_argument('--max-frames', type=int, default=30,
                       help='最大帧数')
    parser.add_argument('--resolution', 
                       choices=['original', '1080p', '720p', '480p', '360p', '240p'],
                       default='original',
                       help='输出图像分辨率')
    parser.add_argument('--base64', action='store_true',
                       help='返回base64编码（用于AI分析）')
    parser.add_argument('--save-files', action='store_true',
                       help='保存图像文件到磁盘')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # 验证参数
    if args.save_files and not args.output:
        parser.error("当使用 --save-files 时必须指定 -o/--output 输出目录")
    
    if not args.base64 and not args.save_files:
        logger.warning("既未指定 --base64 也未指定 --save-files，将默认启用 --base64")
        args.base64 = True
    
    # 处理参数
    try:
        k = int(args.keyframes) if args.keyframes != 'auto' else 'auto'
    except ValueError:
        k = 'auto'
    
    result = extract_top_k_keyframes(
        args.input, 
        args.output, 
        k=k,
        adaptive_mode=args.mode,
        interval=args.interval,
        frames_per_interval=args.frames_per_interval,
        min_frames=args.min_frames,
        max_frames=args.max_frames,
        resolution=args.resolution,
        return_base64=args.base64,
        save_files=args.save_files
    )
    
    if 'error' in result:
        logger.error(f"错误: {result['error']}")
        sys.exit(1)
    
    # 输出base64结果（用于Azure OpenAI分析）
    if args.base64:
        print("\n" + "="*50)
        print("Azure OpenAI 分析用 Base64 数据:")
        print("="*50)
        for i, frame in enumerate(result['frames']):
            if 'base64' in frame:
                print(f"\n帧 {i+1} (时间: {frame['timestamp']:.1f}s):")
                print(f"data:image/jpeg;base64,{frame['base64'][:100]}...")
                print(f"完整长度: {len(frame['base64'])} 字符")


if __name__ == "__main__":
    main()
