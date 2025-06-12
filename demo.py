#!/usr/bin/env python3
"""
智能关键帧提取器 - 完整演示脚本
展示从视频提取到AI分析的完整工作流程
"""

import os
import sys
import json
from pathlib import Path

# 添加包路径
sys.path.insert(0, str(Path(__file__).parent))

from smart_keyframe_extractor import extract_top_k_keyframes
from smart_keyframe_extractor.azure_openai import AzureOpenAIAnalyzer

def main():
    print("🎬 智能关键帧提取器 - 完整演示")
    print("=" * 50)
    
    # 检查环境
    video_path = "videos/784943.mp4"
    if not os.path.exists(video_path):
        print(f"❌ 演示视频不存在: {video_path}")
        return
    
    # 检查Azure配置
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        print("⚠️  Azure OpenAI 未配置，将仅展示关键帧提取功能")
        ai_enabled = False
    else:
        ai_enabled = True
        print("✅ Azure OpenAI 已配置")
    
    print()
    
    # 演示1：基础提取
    print("📋 演示1：基础关键帧提取")
    print("-" * 30)
    
    result = extract_top_k_keyframes(
        video_path=video_path,
        k=4,
        resolution="720p",
        return_base64=True,
        save_files=False
    )
    
    if 'error' in result:
        print(f"❌ 提取失败: {result['error']}")
        return
    
    frames = result['frames']
    print(f"✅ 成功提取 {len(frames)} 个关键帧")
    print(f"📽️  视频信息: {result['video_duration']:.1f}秒, {result['original_resolution']}")
    print(f"🔧 处理参数: {result['resolution']}, {result['adaptive_mode']} 模式")
    print()
    
    for i, frame in enumerate(frames):
        print(f"   帧 {i+1}: {frame['timestamp']:.1f}s, "
              f"变化分数 {frame['change_score']:.1f}, "
              f"Base64: {len(frame.get('base64', ''))} 字符")
    
    print()
    
    # 演示2：自适应模式
    print("📋 演示2：自适应模式")
    print("-" * 30)
    
    adaptive_result = extract_top_k_keyframes(
        video_path=video_path,
        k="auto",
        adaptive_mode="adaptive",
        resolution="480p",
        return_base64=True
    )
    
    adaptive_frames = adaptive_result['frames']
    print(f"🤖 自适应计算: {len(adaptive_frames)} 帧 (原始 {adaptive_result['total_frames_analyzed']} 帧)")
    print(f"⏱️  平均间隔: {adaptive_result['video_duration']/len(adaptive_frames):.1f}秒/帧")
    print()
    
    # 演示3：AI分析（如果可用）
    if ai_enabled:
        print("📋 演示3：Azure OpenAI 智能分析")
        print("-" * 30)
        
        try:
            analyzer = AzureOpenAIAnalyzer()
            
            # 分析基础提取的帧
            analysis = analyzer.analyze_video_frames(
                frames=frames,
                custom_prompt="""
                请作为视频内容分析专家，详细分析这些关键帧：
                1. 描述每一帧的主要内容和场景
                2. 分析视频的整体主题和情节发展
                3. 识别关键对象和它们的行为模式
                4. 总结视频的核心信息
                """,
                max_tokens=800
            )
            
            if analysis['success']:
                print(f"🤖 AI分析成功完成")
                print(f"📊 Token使用: {analysis['usage']['total_tokens']} "
                      f"(提示: {analysis['usage']['prompt_tokens']}, "
                      f"回复: {analysis['usage']['completion_tokens']})")
                print()
                print("🎯 AI分析结果:")
                print("-" * 20)
                print(analysis['analysis'])
                print("-" * 20)
                
                # 保存完整分析结果
                full_result = {
                    'extraction_result': result,
                    'ai_analysis': analysis,
                    'metadata': {
                        'timestamp': str(Path(__file__).stat().st_mtime),
                        'version': '1.0.0'
                    }
                }
                
                output_file = 'demo_analysis_result.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(full_result, f, ensure_ascii=False, indent=2)
                print(f"\n💾 完整结果已保存到: {output_file}")
                
            else:
                print(f"❌ AI分析失败: {analysis.get('error')}")
                
        except Exception as e:
            print(f"❌ AI分析异常: {e}")
    
    print()
    print("🎉 演示完成！")
    print()
    print("💡 使用建议:")
    print("   • 对于短视频(<30s)使用自适应模式")
    print("   • 对于长视频使用间隔模式")
    print("   • 根据用途选择合适的分辨率")
    print("   • 自定义AI提示词获得更精准的分析")
    print()
    print("📚 更多信息请查看 README.md")

if __name__ == "__main__":
    main()
