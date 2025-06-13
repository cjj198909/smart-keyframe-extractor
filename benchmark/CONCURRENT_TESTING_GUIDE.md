# 并发压力测试使用指南

## 🎯 功能概述

本压力测试套件为Smart Keyframe Extractor提供了全面的并发和大规模测试能力，特别适合云服务器环境下的性能验证。

## 📦 测试工具一览

### 1. 本地开发测试工具
- `quick_benchmark.py` - 快速性能基准测试
- `memory_stress_test.py` - 内存泄漏和稳定性测试
- `stress_test.py` - 全面性能分析（需要matplotlib）

### 2. 并发压力测试工具
- `concurrent_stress_test.py` - 多线程并发测试核心
- `cloud_stress_test.py` - 云服务器专用启动器

### 3. 云服务器部署工具
- `deploy_cloud_stress_test.sh` - 一键部署脚本

## 🚀 快速开始

### 本地测试
```bash
# 统一入口
python benchmark/run_tests.py

# 或直接运行
python benchmark/quick_benchmark.py
python benchmark/memory_stress_test.py
```

### 云服务器测试
```bash
# 1. 部署环境
bash deploy_cloud_stress_test.sh

# 2. 运行基础并发测试
python benchmark/cloud_stress_test.py --video-dirs /path/to/videos

# 3. 运行高强度压力测试
python benchmark/cloud_stress_test.py \
  --video-dirs /path/to/videos \
  --test-profile stress \
  --max-workers 32 \
  --iterations 5
```

## 🔧 详细配置选项

### 并发测试参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--video-dirs` | 视频文件目录列表 | 必需 | `/data/videos /backup/videos` |
| `--max-workers` | 最大并发线程数 | CPU核心数+4 | `16` |
| `--test-profile` | 测试配置档案 | standard | `comprehensive` |
| `--iterations` | 每配置迭代次数 | 1 | `3` |
| `--test-mode` | 测试模式 | concurrent | `both` |
| `--duration` | 持续测试时长(分钟) | 30 | `60` |
| `--target-qps` | 目标QPS | 2.0 | `5.0` |

### 测试配置档案

#### minimal - 最小测试
```json
[
  {"name": "minimal_test", "k": 3, "frame_skip": 3, "resolution": "480p"}
]
```

#### standard - 标准测试
```json
[
  {"name": "standard_low", "k": 5, "frame_skip": 2, "resolution": "720p"},
  {"name": "standard_high", "k": 5, "frame_skip": 1, "resolution": "original"}
]
```

#### comprehensive - 全面测试
```json
[
  {"name": "ultra_fast", "k": 3, "frame_skip": 5, "resolution": "480p"},
  {"name": "fast", "k": 5, "frame_skip": 3, "resolution": "720p"},
  {"name": "balanced", "k": 5, "frame_skip": 2, "resolution": "720p"},
  {"name": "high_quality", "k": 10, "frame_skip": 1, "resolution": "original"},
  {"name": "max_quality", "k": 15, "frame_skip": 1, "resolution": "original"}
]
```

#### stress - 高强度压力测试
```json
[
  {"name": "stress_1", "k": 5, "frame_skip": 1, "resolution": "original"},
  {"name": "stress_2", "k": 10, "frame_skip": 1, "resolution": "original"},
  {"name": "stress_3", "k": 15, "frame_skip": 1, "resolution": "original"},
  {"name": "stress_4", "k": 20, "frame_skip": 1, "resolution": "original"}
]
```

## 📊 测试场景示例

### 1. 基础功能验证
```bash
# 验证基本功能是否正常
python benchmark/cloud_stress_test.py \
  --video-dirs ./videos \
  --test-profile minimal \
  --dry-run
```

### 2. 并发性能测试
```bash
# 测试多线程并发处理能力
python benchmark/cloud_stress_test.py \
  --video-dirs /data/videos \
  --test-profile standard \
  --max-workers 16 \
  --iterations 3
```

### 3. 持续负载测试
```bash
# 测试长时间稳定运行能力
python benchmark/cloud_stress_test.py \
  --video-dirs /data/videos \
  --test-mode sustained \
  --duration 60 \
  --target-qps 3.0
```

### 4. 极限压力测试
```bash
# 测试系统极限处理能力
python benchmark/cloud_stress_test.py \
  --video-dirs /data/videos \
  --test-profile stress \
  --max-workers 64 \
  --test-mode both \
  --duration 120 \
  --target-qps 10.0
```

### 5. 自定义配置测试
```bash
# 使用自定义配置文件
python benchmark/cloud_stress_test.py \
  --video-dirs /data/videos \
  --custom-config my_config.json \
  --max-workers 24
```

## 📈 结果分析

### 自动生成的报告
- JSON格式：详细测试数据
- CSV格式：便于Excel分析
- 汇总报告：总体性能指标

### 关键性能指标
- **成功率**: 任务完成成功的百分比
- **执行时间**: 平均、最小、最大处理时间
- **内存使用**: 内存峰值和平均使用量
- **吞吐量**: 每秒处理的视频数/帧数
- **系统资源**: CPU、内存、磁盘、网络使用率

### 分析工具
```bash
# 自动分析所有结果
python analyze_results.py

# 查看详细日志
tail -f logs/stress_test_*.log
```

## 🔍 监控和调优

### 系统监控
```bash
# 启动系统资源监控
./monitor_system.sh
```

### 性能调优建议

#### 内存优化
- 如果内存使用过高，减少 `max_workers`
- 使用较低分辨率配置：`480p` 而非 `original`
- 增加 `frame_skip` 值减少内存消耗

#### CPU优化
- 根据CPU核心数调整 `max_workers`
- 一般建议：`max_workers = CPU核心数 × 1.5 - 2`
- 对于I/O密集型任务可以设置更高

#### 网络优化
- 确保视频文件在本地存储
- 避免通过网络访问视频文件
- 使用SSD存储提高I/O性能

## 🐛 故障排除

### 常见问题

#### 1. 内存不足 (OOM)
```bash
# 解决方案：减少并发数
python benchmark/cloud_stress_test.py \
  --video-dirs /data/videos \
  --max-workers 4 \
  --test-profile minimal
```

#### 2. 文件权限错误
```bash
# 确保文件权限正确
chmod +x *.sh
chmod -R 755 videos/
```

#### 3. 依赖库缺失
```bash
# 安装所需依赖
pip install opencv-python psutil pandas matplotlib
```

#### 4. FFmpeg 未安装
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

### 日志调试
```bash
# 查看详细错误日志
grep -i error logs/stress_test_*.log

# 查看性能日志
grep -i "测试完成\|成功率\|执行时间" logs/stress_test_*.log
```

## 📚 最佳实践

### 1. 测试前准备
- 确保充足的磁盘空间（结果文件可能较大）
- 关闭不必要的服务释放资源
- 备份重要数据

### 2. 测试策略
- 先运行 `minimal` 配置验证环境
- 逐步增加并发数和复杂度
- 长时间测试前先进行短时间验证

### 3. 结果解读
- 关注成功率，应保持在95%以上
- 监控内存增长趋势，避免内存泄漏
- 记录不同配置下的性能基线

### 4. 生产部署建议
- 根据测试结果选择合适的并发数
- 设置合理的超时和重试机制
- 实施监控和告警机制

## 🎯 性能基线参考

基于测试环境的性能基线：

| 配置 | 并发数 | 平均耗时 | 内存使用 | 推荐场景 |
|------|--------|----------|----------|----------|
| minimal | 4-8 | 1-2s | 50-100MB | 功能验证 |
| standard | 8-16 | 2-4s | 100-200MB | 日常使用 |
| comprehensive | 16-32 | 3-6s | 200-400MB | 性能测试 |
| stress | 32-64 | 4-8s | 400-800MB | 极限测试 |

注：具体性能因硬件配置和视频内容而异

## 📞 技术支持

如遇到问题，请提供：
1. 系统配置信息
2. 错误日志文件
3. 使用的测试命令
4. 视频文件信息（格式、大小、时长）
