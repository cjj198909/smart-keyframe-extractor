#!/usr/bin/env python3
"""
内存压力测试工具 - 测试大量连续处理的内存泄漏情况
"""

import time
import psutil
import os
import sys
import gc
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from smart_keyframe_extractor.extractor import extract_top_k_keyframes


class MemoryStressTest:
    """内存压力测试类"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.memory_history = []
    
    def get_memory_usage(self) -> dict:
        """获取当前内存使用情况"""
        memory_info = self.process.memory_info()
        return {
            "rss": memory_info.rss / (1024**2),  # MB
            "vms": memory_info.vms / (1024**2),  # MB
            "percent": self.process.memory_percent(),
            "timestamp": time.time()
        }
    
    def continuous_processing_test(self, video_path: str, iterations: int = 50):
        """连续处理测试，检查内存泄漏"""
        print(f"🔄 开始连续处理测试: {iterations} 次迭代")
        print(f"📹 测试视频: {video_path}")
        
        if not os.path.exists(video_path):
            print(f"❌ 视频文件不存在: {video_path}")
            return
        
        initial_memory = self.get_memory_usage()
        print(f"🏁 初始内存使用: {initial_memory['rss']:.1f}MB")
        
        self.memory_history = [initial_memory]
        
        for i in range(iterations):
            print(f"\r🔄 处理进度: {i+1}/{iterations}", end="", flush=True)
            
            try:
                # 执行关键帧提取
                result = extract_top_k_keyframes(
                    video_path=video_path,
                    k=3,  # 使用较小的K值加快处理
                    resolution='480p',  # 使用较低分辨率
                    return_base64=False,
                    save_files=False
                )
                
                # 强制垃圾回收
                del result
                gc.collect()
                
                # 记录内存使用
                current_memory = self.get_memory_usage()
                self.memory_history.append(current_memory)
                
                # 每10次迭代显示内存状况
                if (i + 1) % 10 == 0:
                    print(f"\n📊 第{i+1}次 - 内存: {current_memory['rss']:.1f}MB "
                          f"(增长: {current_memory['rss'] - initial_memory['rss']:+.1f}MB)")
                
            except Exception as e:
                print(f"\n❌ 第{i+1}次处理失败: {e}")
                continue
        
        final_memory = self.get_memory_usage()
        print(f"\n\n📊 压力测试结果:")
        print(f"🏁 初始内存: {initial_memory['rss']:.1f}MB")
        print(f"🏁 最终内存: {final_memory['rss']:.1f}MB") 
        print(f"📈 总内存增长: {final_memory['rss'] - initial_memory['rss']:+.1f}MB")
        print(f"📈 平均每次增长: {(final_memory['rss'] - initial_memory['rss'])/iterations:+.2f}MB")
        
        # 分析内存趋势
        self.analyze_memory_trend()
        
        return self.memory_history
    
    def analyze_memory_trend(self):
        """分析内存使用趋势"""
        if len(self.memory_history) < 10:
            return
        
        print(f"\n📈 内存趋势分析:")
        
        # 计算内存增长趋势
        memory_values = [m['rss'] for m in self.memory_history]
        
        # 最高内存使用
        max_memory = max(memory_values)
        max_idx = memory_values.index(max_memory)
        print(f"🔝 峰值内存: {max_memory:.1f}MB (第{max_idx+1}次迭代)")
        
        # 内存增长率
        if len(memory_values) >= 20:
            early_avg = sum(memory_values[1:11]) / 10  # 第2-11次的平均
            late_avg = sum(memory_values[-10:]) / 10   # 最后10次的平均
            growth_rate = (late_avg - early_avg) / early_avg * 100
            print(f"📊 内存增长率: {growth_rate:+.1f}%")
            
            if growth_rate > 10:
                print("⚠️  警告: 检测到可能的内存泄漏!")
            elif growth_rate < 5:
                print("✅ 内存使用稳定")
            else:
                print("⚡ 内存使用轻微增长")
    
    def batch_processing_test(self, video_path: str, batch_sizes: list = [1, 5, 10, 20]):
        """批量处理测试，测试不同批量大小的内存表现"""
        print(f"\n🔄 批量处理测试")
        
        for batch_size in batch_sizes:
            print(f"\n📦 批量大小: {batch_size}")
            
            start_memory = self.get_memory_usage()
            start_time = time.time()
            
            for i in range(batch_size):
                try:
                    result = extract_top_k_keyframes(
                        video_path=video_path,
                        k=3,
                        resolution='480p',
                        return_base64=False,
                        save_files=False
                    )
                    del result
                except Exception as e:
                    print(f"❌ 批量处理失败: {e}")
                    break
            
            # 强制垃圾回收
            gc.collect()
            
            end_memory = self.get_memory_usage()
            end_time = time.time()
            
            memory_increase = end_memory['rss'] - start_memory['rss']
            total_time = end_time - start_time
            
            print(f"   ⏱️  总耗时: {total_time:.1f}s")
            print(f"   💾 内存增长: {memory_increase:+.1f}MB")
            print(f"   📊 每个任务内存: {memory_increase/batch_size:.2f}MB")
            print(f"   🚀 平均速度: {batch_size/total_time:.1f} 任务/秒")


def main():
    """主函数"""
    print("💪 Smart Keyframe Extractor - 内存压力测试")
    print("=" * 50)
    
    # 检查测试视频
    test_video = "videos/785023.mp4"
    if not os.path.exists(test_video):
        print(f"❌ 测试视频不存在: {test_video}")
        print("请将测试视频放在 videos/ 目录下")
        return
    
    stress_tester = MemoryStressTest()
    
    try:
        print("\n请选择测试类型:")
        print("1. 连续处理测试 (检查内存泄漏)")
        print("2. 批量处理测试 (不同批量大小)")
        print("3. 完整压力测试")
        
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            iterations = int(input("请输入测试迭代次数 (默认30): ") or "30")
            stress_tester.continuous_processing_test(test_video, iterations)
            
        elif choice == "2":
            stress_tester.batch_processing_test(test_video)
            
        elif choice == "3":
            print("\n🚀 开始完整压力测试...")
            stress_tester.continuous_processing_test(test_video, 30)
            stress_tester.batch_processing_test(test_video)
            
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
