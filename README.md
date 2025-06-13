# Smart Keyframe Extractor

🎯 **智能视频关键帧提取工具** - 支持自适应模式、多分辨率输出和 Azure OpenAI 智能分析

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-red)](https://ffmpeg.org/)
[![Stress Tests](https://img.shields.io/badge/Stress%20Tests-✅%20Passed-brightgreen)](STRESS_TEST_COMPLETION_SUMMARY.md)
[![Production Ready](https://img.shields.io/badge/Production-Ready-success)](PERFORMANCE_ANALYSIS_REPORT.md)

## ✨ 功能特性

- 🎯 **智能关键帧提取**: 使用光流、场景变化、颜色变化等多重算法分析
- 🔄 **自适应模式**: 根据视频时长自动计算最佳帧数
- 📐 **多分辨率支持**: 支持多种输出分辨率 (1080p, 720p, 480p, 360p, 240p)
- 🌐 **Base64编码输出**: 直接输出base64格式，便于AI分析
- ☁️ **远程视频支持**: 支持HTTP/HTTPS URL、AWS S3、Azure Blob Storage、Google Cloud Storage
- 🤖 **Azure OpenAI集成**: 内置Azure OpenAI Vision API支持
- ⚡ **高性能处理**: 优化的FFmpeg集成和并行处理
- 📱 **跨平台支持**: 支持 Windows、macOS 和 Linux

## 🚀 快速体验

想要快速体验完整功能？运行我们的交互式演示：

```bash
# 克隆项目
git clone https://github.com/cjj198909/smart-keyframe-extractor.git
cd smart-keyframe-extractor

# 安装依赖
pip install -e .

# 启动 Jupyter Notebook 演示
./start_notebook_demo.sh
```

> 💡 演示 notebook 包含完整的功能展示、性能分析和最佳实践指南

## 安装

### 🎯 选择安装方式

#### 1. 基础安装（本地视频处理）
```bash
pip install smart-keyframe-extractor
```

#### 2. 包含远程视频支持（推荐）
```bash
# 安装所有功能（包含云存储支持）
pip install smart-keyframe-extractor[all]

# 或者分步安装
pip install smart-keyframe-extractor[remote]  # 仅远程视频支持
```

#### 3. 包含Azure OpenAI支持
```bash
pip install smart-keyframe-extractor[azure]
```

#### 4. 开发者安装
```bash
git clone https://github.com/cjj198909/smart-keyframe-extractor.git
cd smart-keyframe-extractor
pip install -e .[all]
```

### 📦 依赖说明

**核心依赖**（自动安装）：
- `opencv-python>=4.5.0` - 视频处理
- `Pillow>=8.0.0` - 图像处理  
- `numpy>=1.19.0` - 数值计算
- `requests>=2.28.0` - HTTP请求

**远程视频支持**（可选）：
- `boto3>=1.26.0` - AWS S3支持
- `azure-storage-blob>=12.14.0` - Azure Blob存储支持
- `google-cloud-storage>=2.7.0` - Google Cloud存储支持

**Azure OpenAI支持**（可选）：
- `openai>=1.0.0` - Azure OpenAI集成

## 系统依赖

确保系统已安装 FFmpeg:

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
下载并安装 FFmpeg from https://ffmpeg.org/download.html

## 快速开始

### 命令行使用

```bash
# 基础使用 - 提取5帧，720p分辨率，输出base64
smart-keyframe video.mp4 -k 5 --resolution 720p --base64

# 自适应模式 - 根据视频长度自动决定帧数
smart-keyframe video.mp4 -k auto --resolution 480p --base64

# 间隔模式 - 每10秒提取1帧
smart-keyframe video.mp4 --mode interval --interval 10 --frames-per-interval 1 --base64

# 远程视频处理 - HTTP/HTTPS URL
smart-keyframe https://example.com/video.mp4 -k 5 --resolution 720p --base64

# 云存储视频处理 - AWS S3
smart-keyframe s3://my-bucket/video.mp4 -k auto --resolution 480p --base64

# 同时保存文件和base64
smart-keyframe video.mp4 -o output_frames -k 8 --resolution 720p --base64 --save-files
```

### Python API使用

#### 基础关键帧提取

```python
from smart_keyframe_extractor import extract_top_k_keyframes

# 提取关键帧并返回base64
result = extract_top_k_keyframes(
    video_path="video.mp4",
    k=5,
    resolution="720p",
    return_base64=True,
    save_files=False
)

# 检查结果
if 'error' not in result:
    print(f"成功提取 {result['extracted_frames']} 帧")
    for frame in result['frames']:
        print(f"帧 {frame['frame_idx']}: 时间 {frame['timestamp']:.1f}s")
        print(f"Base64长度: {len(frame['base64'])}")
```

#### 自适应模式

```python
# 自适应模式 - 根据视频时长自动决定帧数
result = extract_top_k_keyframes(
    video_path="long_video.mp4",
    k="auto",
    adaptive_mode="adaptive",
    min_frames=3,
    max_frames=20,
    resolution="480p",
    return_base64=True
)
```

#### 间隔模式

```python
# 间隔模式 - 每15秒提取2帧
result = extract_top_k_keyframes(
    video_path="video.mp4",
    adaptive_mode="interval",
    interval=15.0,
    frames_per_interval=2,
    resolution="720p",
    return_base64=True
)
```

#### 远程视频处理

```python
# HTTP/HTTPS URL
result = extract_top_k_keyframes(
    video_path="https://example.com/video.mp4",
    k=5,
    resolution="720p",
    return_base64=True
)

# AWS S3 (需要配置AWS凭证)
result = extract_top_k_keyframes(
    video_path="s3://my-bucket/video.mp4",
    k="auto",
    resolution="480p",
    return_base64=True
)

# Azure Blob Storage (需要配置Azure存储凭证)
result = extract_top_k_keyframes(
    video_path="https://myaccount.blob.core.windows.net/container/video.mp4",
    k=5,
    resolution="720p",
    return_base64=True
)

# Google Cloud Storage (需要配置GCP凭证)
result = extract_top_k_keyframes(
    video_path="gs://my-bucket/video.mp4",
    k="auto",
    resolution="720p",
    return_base64=True
)
```

### Azure OpenAI 集成

#### 设置环境变量

```bash
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
```

#### 完整视频分析

```python
from smart_keyframe_extractor.azure_openai import analyze_video_with_azure_openai

# 完整的视频分析流程
result = analyze_video_with_azure_openai(
    video_path="video.mp4",
    k=6,
    resolution="720p",
    custom_prompt="请详细分析这个视频的内容和情节发展"
)

if result['success']:
    print("AI分析结果:")
    print(result['video_analysis']['analysis'])
    print(f"使用token数: {result['video_analysis']['usage']['total_tokens']}")
else:
    print(f"分析失败: {result['error']}")
```

#### 完整视频分析流程（支持detail参数）

```python
from smart_keyframe_extractor.azure_openai import analyze_video_with_azure_openai

# 高精度完整分析
result = analyze_video_with_azure_openai(
    video_path="video.mp4",
    k=5,
    resolution="720p",
    custom_prompt="请详细分析这个视频的内容、场景和主要对象",
    detail="high",  # 高精度分析
    adaptive_mode="adaptive"
)

# 快速批量分析
result = analyze_video_with_azure_openai(
    video_path="video.mp4", 
    k=3,
    resolution="480p",
    custom_prompt="请简要描述视频内容",
    detail="low",  # 快速分析模式
    adaptive_mode="interval",
    interval=10.0
)

if result['success']:
    print("✅ 分析成功")
    print(f"📊 提取帧数: {result['keyframe_extraction']['extracted_frames']}")
    print(f"🔍 使用tokens: {result['video_analysis']['usage']['total_tokens']}")
    print(f"📝 分析结果: {result['video_analysis']['analysis']}")
else:
    print(f"❌ 分析失败: {result['error']}")
```

#### 单独使用Azure OpenAI分析器

```python
from smart_keyframe_extractor.azure_openai import AzureOpenAIAnalyzer

# 首先提取关键帧
keyframes_result = extract_top_k_keyframes(
    video_path="video.mp4",
    k=5,
    return_base64=True
)

# 然后进行AI分析
analyzer = AzureOpenAIAnalyzer(
    api_key="your-api-key",
    endpoint="https://your-resource.openai.azure.com/"
)

analysis = analyzer.analyze_video_frames(
    frames=keyframes_result['frames'],
    custom_prompt="分析这些关键帧中的主要活动和场景变化"
)

print(analysis['analysis'])
```

## 高级功能

### 自定义提取器

```python
from smart_keyframe_extractor import SmartKeyFrameExtractor

extractor = SmartKeyFrameExtractor()

# 获取视频信息
video_info = extractor.get_video_info("video.mp4")
print(f"视频时长: {video_info['duration']:.1f}秒")

# 计算帧变化
frame_changes, video_info = extractor.compute_frame_changes("video.mp4")

# 选择最佳帧
selected_frames = extractor.select_global_top_k_frames(frame_changes, k=8)

# 提取并转换为base64
extracted_frames = extractor.extract_frames_with_ffmpeg(
    video_path="video.mp4",
    frame_info_list=selected_frames,
    resolution="720p",
    return_base64=True
)
```

### 批量处理

```python
from smart_keyframe_extractor.azure_openai import AzureOpenAIAnalyzer

# 批量处理多个视频
video_files = ["video1.mp4", "video2.mp4", "video3.mp4"]
results = []

for video_file in video_files:
    result = extract_top_k_keyframes(
        video_path=video_file,
        k=5,
        resolution="720p",
        return_base64=True
    )
    results.append(result)

# 批量AI分析
analyzer = AzureOpenAIAnalyzer()
analyses = analyzer.batch_analyze_videos(results)

for analysis in analyses:
    if analysis['success']:
        print(f"视频: {analysis['video_path']}")
        print(f"分析: {analysis['analysis'][:200]}...")
```

## 🌐 远程视频支持

### 支持的存储类型

- **HTTP/HTTPS URL**: 直接支持，无需额外配置
- **AWS S3**: 需要配置AWS凭证
- **Azure Blob Storage**: 需要配置Azure存储凭证  
- **Google Cloud Storage**: 需要配置GCP凭证

### 依赖安装

```bash
# 安装所有远程视频依赖
pip install requests boto3 azure-storage-blob google-cloud-storage

# 或按需安装
pip install requests                    # HTTP/HTTPS支持
pip install boto3                      # AWS S3支持
pip install azure-storage-blob         # Azure Blob支持
pip install google-cloud-storage       # Google Cloud支持
```

### 云服务配置

#### AWS S3配置

```bash
# 方法1: 使用AWS CLI
aws configure

# 方法2: 环境变量
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

#### Azure Blob Storage配置

```bash
# 方法1: 连接字符串
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"

# 方法2: 账户名+密钥
export AZURE_STORAGE_ACCOUNT_NAME="your-account-name"
export AZURE_STORAGE_ACCOUNT_KEY="your-account-key"
```

#### Google Cloud Storage配置

```bash
# 方法1: 使用gcloud CLI
gcloud auth login

# 方法2: 服务账户密钥
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 缓存配置

```bash
# 设置自定义缓存目录
export REMOTE_VIDEO_CACHE_DIR="/path/to/cache/directory"
```

### 配置检查

运行配置检查脚本来验证设置：

```bash
python scripts/setup_remote_video.py
```

## 参数说明

### extract_top_k_keyframes 参数

- `video_path`: 视频文件路径
- `k`: 提取的帧数，可以是数字或 "auto"
- `adaptive_mode`: 自适应模式 ("fixed", "adaptive", "interval")
- `interval`: 时间间隔（秒），用于interval模式
- `frames_per_interval`: 每个间隔提取的帧数
- `min_frames`/`max_frames`: 最小/最大帧数限制
- `resolution`: 输出分辨率 ("original", "1080p", "720p", "480p", "360p", "240p")
- `return_base64`: 是否返回base64编码
- `save_files`: 是否保存图像文件

### 分辨率选择

- `original`: 保持原始分辨率
- `1080p`: 1920x1080
- `720p`: 1280x720  
- `480p`: 854x480
- `360p`: 640x360
- `240p`: 426x240

### Detail 参数控制

Azure OpenAI 分析支持 `detail` 参数来控制图像分析的精度和token消耗：

```python
from smart_keyframe_extractor.azure_openai import AzureOpenAIAnalyzer

analyzer = AzureOpenAIAnalyzer()

# 高精度模式 - 更详细的分析，消耗更多tokens
analysis_high = analyzer.analyze_video_frames(
    frames=frames,
    custom_prompt="请详细分析这些图像",
    detail="high"
)

# 低精度模式 - 快速分析，消耗较少tokens，适合批量处理
analysis_low = analyzer.analyze_video_frames(
    frames=frames,
    custom_prompt="请简要分析这些图像", 
    detail="low"
)

# 自动模式 - 系统自动选择最佳模式
analysis_auto = analyzer.analyze_video_frames(
    frames=frames,
    custom_prompt="请分析这些图像",
    detail="auto"
)
```

#### Detail 参数说明

- `"high"` (默认): 高精度分析，提供更多细节，适合需要精确识别的场景
- `"low"`: 快速分析，消耗更少tokens，适合批量处理或预览
- `"auto"`: 自动选择，根据图像复杂度智能调整分析精度

#### 使用建议

1. **批量处理**: 使用 `detail="low"` 节省成本和时间
2. **精细分析**: 使用 `detail="high"` 获得最佳分析质量
3. **平衡使用**: 使用 `detail="auto"` 让系统自动优化

## 🏆 生产环境验证

**✅ 大规模压力测试已完成！**

- **测试规模**: 大规模视频文件，企业级处理任务
- **成功率**: 100% (全部成功) 
- **平均性能**: 30.1秒/视频，96.4% CPU利用率
- **内存效率**: 无内存泄漏，平均8.9MB增长
- **并发能力**: 8个worker稳定并发处理

📊 [查看详细性能分析报告](PERFORMANCE_ANALYSIS_REPORT.md) | 📋 [压力测试完成总结](STRESS_TEST_COMPLETION_SUMMARY.md)

## 🧪 基准测试和压力测试

项目包含完整的测试套件，支持性能基准测试和大规模压力测试：

```bash
# 快速基准测试
python benchmark/quick_benchmark.py

# 并发压力测试
python benchmark/concurrent_stress_test.py --max-workers 8

# 云服务器一键部署测试
bash deploy_cloud_stress_test.sh

# 智能性能分析
python benchmark/performance_optimizer.py --report-only

# 分支性能对比
python benchmark/branch_comparator.py --base-branch main --compare-branch feature
```

📚 [查看完整测试指南](STRESS_TESTING_GUIDE.md) | 🔧 [并发测试指南](benchmark/CONCURRENT_TESTING_GUIDE.md)

## 性能优化

1. **降采样处理**: 分析时使用0.25倍分辨率加速处理
2. **智能间隔**: 自动计算最佳时间间隔避免重复帧
3. **FFmpeg优化**: 直接使用FFmpeg提取高质量帧
4. **内存管理**: 临时文件自动清理

## 错误处理

```python
result = extract_top_k_keyframes("video.mp4", k=5)

if 'error' in result:
    print(f"提取失败: {result['error']}")
else:
    print(f"成功提取 {result['extracted_frames']} 帧")
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0 (2025-06-13) - 压力测试版本 🎉
- ✅ **大规模压力测试完成**: 企业级多视频文件测试，100%成功率
- 🚀 **并发处理优化**: 支持最高64个worker并发
- 🔧 **智能性能分析**: 自动配置优化和分支对比工具
- 🌐 **云服务器支持**: 一键部署脚本，支持Ubuntu/CentOS
- 📊 **完整测试套件**: 基准测试、内存测试、并发测试
- 🤖 **AI集成优化**: detail参数优化，支持low/high/auto模式
- 📋 **生产就绪**: 经过大规模真实数据验证

### v0.1.0
- 初始版本发布
- 支持智能关键帧提取
- 集成Azure OpenAI Vision API
- 支持多种分辨率输出
- 支持base64编码输出
