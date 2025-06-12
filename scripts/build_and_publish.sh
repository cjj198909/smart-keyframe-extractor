#!/bin/bash
# 发布脚本 - 构建并发布到PyPI

set -e  # 遇到错误时退出

echo "🚀 开始构建和发布 smart-keyframe-extractor..."

# 清理之前的构建文件
echo "🧹 清理构建文件..."
rm -rf build/ dist/ *.egg-info/

# 构建包
echo "📦 构建包..."
python -m build

# 检查包
echo "🔍 检查包..."
python -m twine check dist/*

echo "✅ 构建完成！"
echo ""
echo "📦 生成的文件:"
ls -la dist/

echo ""
echo "🚀 发布到PyPI的步骤:"
echo "1. 确保已安装 twine: pip install twine"
echo "2. 上传到测试PyPI (可选): twine upload --repository testpypi dist/*"
echo "3. 上传到正式PyPI: twine upload dist/*"
echo ""
echo "💡 提示："
echo "- 首次上传需要PyPI账号和API token"
echo "- 建议先上传到测试PyPI验证"
echo "- 版本号需要是唯一的"
