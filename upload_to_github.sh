#!/bin/bash

# GitHub 上传脚本
# 请先在 GitHub 创建名为 smart-keyframe-extractor 的新仓库

echo "🚀 正在上传 Smart Keyframe Extractor 到 GitHub..."

# 添加远程仓库
echo "📡 添加远程仓库..."
git remote add origin https://github.com/cjj198909/smart-keyframe-extractor.git

# 设置主分支
echo "🌿 设置主分支..."
git branch -M main

# 推送到 GitHub
echo "⬆️ 推送到 GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 成功上传到 GitHub！"
    echo "📍 仓库地址: https://github.com/cjj198909/smart-keyframe-extractor"
    echo ""
    echo "✨ 你的仓库包含："
    echo "   - 完整的智能关键帧提取工具"
    echo "   - 交互式 Jupyter Notebook 演示"
    echo "   - Azure OpenAI 集成功能"
    echo "   - 完整的文档和示例"
    echo "   - 开箱即用的代码"
    echo ""
    echo "🔗 下一步: 访问你的 GitHub 仓库查看完整项目"
else
    echo "❌ 上传失败，请检查："
    echo "   1. 是否已在 GitHub 创建了 smart-keyframe-extractor 仓库"
    echo "   2. 网络连接是否正常"
    echo "   3. GitHub 认证是否配置正确"
fi
