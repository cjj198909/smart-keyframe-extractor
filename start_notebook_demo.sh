#!/bin/bash

# Smart Keyframe Extractor Notebook 启动脚本

echo "🚀 启动 Smart Keyframe Extractor 完整演示 Notebook"
echo "================================================"

# 检查是否在正确的目录
if [ ! -f "test_detail_notebook.ipynb" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

echo "📋 准备启动 Jupyter Notebook..."

# 检查依赖
echo "🔍 检查Python环境..."
python3 -c "import sys; print(f'Python版本: {sys.version}')"

echo "🔍 检查必要的包..."
python3 -c "
try:
    import numpy, cv2, PIL
    print('✅ 基础依赖包已安装')
except ImportError as e:
    print(f'❌ 缺少依赖包: {e}')
    exit(1)

try:
    from smart_keyframe_extractor import extract_top_k_keyframes
    print('✅ Smart Keyframe Extractor 已安装')
except ImportError:
    print('❌ Smart Keyframe Extractor 未安装，请先运行: pip install -e .')
    exit(1)
"

# 检查视频文件
if [ ! -f "videos/785023.mp4" ]; then
    echo "⚠️ 演示视频文件不存在，notebook中的某些功能可能无法运行"
    echo "请确保 videos/785023.mp4 文件存在"
fi

echo ""
echo "📝 Notebook 内容概览:"
echo "   1. 环境配置和检查"
echo "   2. 基础关键帧提取演示"
echo "   3. 自适应模式对比"
echo "   4. Azure OpenAI 智能分析 (需要API配置)"
echo "   5. 性能分析和优化建议"
echo "   6. 高级功能展示"
echo "   7. 最佳实践指南"
echo ""

echo "🌐 启动 Jupyter Notebook..."
echo "浏览器将自动打开，如果没有，请手动访问显示的URL"
echo ""

# 启动 Jupyter Notebook
jupyter notebook test_detail_notebook.ipynb

echo "📝 Notebook 已关闭"
echo "感谢使用 Smart Keyframe Extractor！"
