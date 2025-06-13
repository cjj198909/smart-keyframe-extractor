#!/usr/bin/env python3
"""
Smart Keyframe Extractor - 基准测试套件
统一的测试入口点
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """主函数"""
    print("🚀 Smart Keyframe Extractor - 基准测试套件")
    print("=" * 60)
    
    print("\n可用的测试工具:")
    print("1. 快速基准测试 - 基本性能和配置对比")
    print("2. 内存压力测试 - 检查内存泄漏和批量处理")
    print("3. 完整压力测试 - 全面的性能分析 (需要额外依赖)")
    print("4. 退出")
    
    try:
        choice = input("\n请选择测试工具 (1-4): ").strip()
        
        if choice == "1":
            print("\n🚀 启动快速基准测试...")
            from benchmark.quick_benchmark import main as quick_main
            quick_main()
            
        elif choice == "2":
            print("\n🚀 启动内存压力测试...")
            from benchmark.memory_stress_test import main as memory_main
            memory_main()
            
        elif choice == "3":
            print("\n🚀 启动完整压力测试...")
            try:
                from benchmark.stress_test import main as stress_main
                stress_main()
            except ImportError as e:
                print(f"❌ 缺少依赖库: {e}")
                print("请安装: pip install matplotlib pandas")
                
        elif choice == "4":
            print("👋 再见!")
            return
            
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n👋 再见!")
    except Exception as e:
        print(f"❌ 发生错误: {e}")


if __name__ == "__main__":
    main()
