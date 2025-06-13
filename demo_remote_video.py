#!/usr/bin/env python3
"""
远程视频处理演示
展示如何使用Smart Keyframe Extractor处理远程视频
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smart_keyframe_extractor import extract_top_k_keyframes, is_remote_url

def demo_http_video():
    """演示HTTP视频处理"""
    print("🌐 HTTP/HTTPS 远程视频处理演示")
    print("=" * 50)
    
    # 使用一个小的示例视频
    test_url = "https://download.samplelib.com/mp4/sample-5s.mp4"
    
    print(f"视频URL: {test_url}")
    print(f"URL检测结果: {'远程视频' if is_remote_url(test_url) else '本地视频'}")
    
    try:
        print("\n📊 开始处理视频...")
        result = extract_top_k_keyframes(
            video_path=test_url,
            k=5,
            resolution="720p",
            return_base64=True,
            save_files=False
        )
        
        if 'error' not in result:
            print(f"✅ 处理成功!")
            print(f"📹 视频时长: {result['video_duration']:.1f}秒")
            print(f"📐 原始分辨率: {result['original_resolution']}")
            print(f"🎯 提取帧数: {result['extracted_frames']}")
            print(f"📊 分析帧数: {result['total_frames_analyzed']}")
            
            print(f"\n🖼️ 关键帧详情:")
            for i, frame in enumerate(result['frames'], 1):
                print(f"  帧 {i}: 时间 {frame['timestamp']:.1f}s, "
                      f"变化分数 {frame['change_score']:.1f}, "
                      f"Base64长度 {len(frame['base64']):,}")
                      
        else:
            print(f"❌ 处理失败: {result['error']}")
            
    except Exception as e:
        print(f"❌ 处理出错: {e}")

def demo_adaptive_mode():
    """演示自适应模式"""
    print("\n🔄 自适应模式演示")
    print("=" * 50)
    
    test_url = "https://download.samplelib.com/mp4/sample-5s.mp4"
    
    try:
        print("📊 使用自适应模式处理视频...")
        result = extract_top_k_keyframes(
            video_path=test_url,
            k="auto",
            adaptive_mode="adaptive",
            min_frames=2,
            max_frames=8,
            resolution="480p",
            return_base64=True
        )
        
        if 'error' not in result:
            print(f"✅ 自适应处理成功!")
            print(f"🔄 自动计算帧数: {result['calculated_frames']}")
            print(f"📊 实际提取帧数: {result['extracted_frames']}")
            print(f"📐 输出分辨率: 480p")
            print(f"📈 最大变化分数: {result['statistics']['max_change_score']:.1f}")
            print(f"📉 平均变化分数: {result['statistics']['avg_change_score']:.1f}")
        else:
            print(f"❌ 自适应处理失败: {result['error']}")
            
    except Exception as e:
        print(f"❌ 处理出错: {e}")

def demo_caching():
    """演示缓存功能"""
    print("\n💾 缓存功能演示")
    print("=" * 50)
    
    from smart_keyframe_extractor.remote_video_utils import RemoteVideoDownloader
    
    try:
        downloader = RemoteVideoDownloader()
        print(f"📁 缓存目录: {downloader.cache_dir}")
        print(f"📏 缓存限制: {downloader.max_cache_size / (1024**3):.1f}GB")
        
        # 检查缓存中的文件
        import os
        if os.path.exists(downloader.cache_dir):
            cached_files = [f for f in os.listdir(downloader.cache_dir) if f.endswith(('.mp4', '.mov', '.avi'))]
            if cached_files:
                print(f"💾 已缓存 {len(cached_files)} 个视频文件")
                total_size = 0
                for filename in cached_files:
                    filepath = os.path.join(downloader.cache_dir, filename)
                    size = os.path.getsize(filepath)
                    total_size += size
                    print(f"  - {filename}: {size / (1024*1024):.1f}MB")
                print(f"📊 总缓存大小: {total_size / (1024*1024):.1f}MB")
            else:
                print("📝 缓存目录为空")
        else:
            print("📝 缓存目录不存在")
            
    except Exception as e:
        print(f"❌ 缓存检查失败: {e}")

def main():
    """主演示函数"""
    print("🎯 Smart Keyframe Extractor - 远程视频处理演示")
    print("=" * 60)
    
    # 检查远程视频支持
    try:
        from smart_keyframe_extractor.remote_video_utils import HAS_REQUESTS
        if not HAS_REQUESTS:
            print("❌ 远程视频功能需要安装 requests 库")
            print("请运行: pip install requests")
            return
        else:
            print("✅ 远程视频支持已启用")
    except ImportError:
        print("❌ 无法导入远程视频模块")
        return
    
    # 运行演示
    demo_http_video()
    demo_adaptive_mode()
    demo_caching()
    
    print("\n" + "=" * 60)
    print("✅ 演示完成!")
    print("\n💡 更多功能:")
    print("• 支持 AWS S3: s3://bucket/video.mp4")
    print("• 支持 Azure Blob: https://account.blob.core.windows.net/container/video.mp4")
    print("• 支持 Google Cloud: gs://bucket/video.mp4")
    print("• 运行配置检查: python scripts/setup_remote_video.py")
    print("• 查看使用示例: python examples/remote_video_example.py")

if __name__ == "__main__":
    main()
