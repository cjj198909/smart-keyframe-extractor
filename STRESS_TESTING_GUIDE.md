# Smart Keyframe Extractor - 完整基准测试和压力测试指南

## 🎯 概述

本项目现在包含了完整的基准测试和压力测试套件，支持从本地开发到云服务器大规模部署的全场景性能测试。

## 📊 测试工具矩阵

| 工具 | 用途 | 并发支持 | 云服务器 | 依赖要求 |
|------|------|----------|----------|----------|
| `quick_benchmark.py` | 快速性能基准 | ❌ | ❌ | 无 |
| `memory_stress_test.py` | 内存泄漏检测 | ❌ | ❌ | psutil |
| `stress_test.py` | 全面性能分析 | ❌ | ❌ | matplotlib, pandas |
| `concurrent_stress_test.py` | 并发压力测试 | ✅ | ❌ | psutil |
| `cloud_stress_test.py` | 云服务器压力测试 | ✅ | ✅ | psutil, pandas |

## 🚀 快速开始

### 1. 本地开发测试
```bash
# 运行统一入口
python benchmark/run_tests.py

# 选择要运行的测试类型
1. 快速基准测试
2. 内存压力测试  
3. 完整压力测试
4. 并发压力测试
5. 云服务器压力测试
```

### 2. 单独运行测试
```bash
# 快速验证功能
python benchmark/quick_benchmark.py

# 检查内存稳定性
python benchmark/memory_stress_test.py

# 并发性能测试
python benchmark/concurrent_stress_test.py --video-dirs videos --max-workers 4

# 云服务器模拟测试
python benchmark/cloud_stress_test.py --video-dirs videos --test-profile standard
```

### 3. 云服务器部署
```bash
# 一键部署（在云服务器上运行）
bash deploy_cloud_stress_test.sh

# 运行压力测试
./run_stress_test.sh /path/to/videos --test-profile comprehensive
```

## 📈 性能基线

基于已完成的测试，以下是主分支的性能基线：

### 基础性能指标
- **执行时间**: 3.2-4.0秒 (单视频5帧提取)
- **内存使用**: 130-135MB
- **处理速度**: 50-55 fps
- **稳定性**: 100%成功率，无内存泄漏

### 并发性能指标
- **并发数**: 2-64个worker (推荐CPU核心数×1.5)
- **平均执行时间**: 3.73秒
- **内存使用**: 132.2MB (平均)
- **CPU使用率**: 41% (2并发)
- **成功率**: 100%

## 🔧 配置选项详解

### 测试配置档案

#### minimal - 快速验证
```json
{"name": "minimal_test", "k": 3, "resolution": "480p"}
```
- 适用场景: 功能验证、CI/CD
- 预期性能: 1-2秒执行时间

#### standard - 生产环境测试
```json
[
  {"name": "standard_low", "k": 5, "resolution": "720p"},
  {"name": "standard_high", "k": 5, "resolution": "original"}
]
```
- 适用场景: 生产环境性能验证
- 预期性能: 3-5秒执行时间

#### comprehensive - 全面测试
```json
[
  {"name": "ultra_fast", "k": 3, "resolution": "480p"},
  {"name": "fast", "k": 5, "resolution": "720p"},
  {"name": "balanced", "k": 5, "resolution": "720p"},
  {"name": "high_quality", "k": 10, "resolution": "original"},
  {"name": "max_quality", "k": 15, "resolution": "original"}
]
```
- 适用场景: 深度性能分析
- 预期性能: 2-8秒执行时间

#### stress - 极限压力测试
```json
[
  {"name": "stress_1", "k": 5, "resolution": "original"},
  {"name": "stress_2", "k": 10, "resolution": "original"},
  {"name": "stress_3", "k": 15, "resolution": "original"},
  {"name": "stress_4", "k": 20, "resolution": "original"}
]
```
- 适用场景: 系统极限测试
- 预期性能: 4-12秒执行时间

## 🌐 云服务器使用

### 环境要求
- Ubuntu 18.04+ 或 CentOS 7+
- Python 3.7+
- 2GB+ 内存
- FFmpeg 支持

### 部署步骤
```bash
# 1. 上传项目到云服务器
scp -r smart_frame/ user@server:/path/to/

# 2. 运行部署脚本
cd /path/to/smart_frame
bash deploy_cloud_stress_test.sh

# 3. 上传测试视频
mkdir -p /data/videos
# 上传视频文件到 /data/videos

# 4. 运行测试
./run_stress_test.sh /data/videos --test-profile comprehensive
```

### 监控和分析
```bash
# 启动系统监控（在另一个终端）
./monitor_system.sh

# 分析测试结果
python analyze_results.py

# 查看日志
tail -f logs/stress_test_*.log
```

## 🔬 测试场景示例

### 1. 功能验证测试
```bash
# 快速验证所有功能是否正常
python benchmark/cloud_stress_test.py \
  --video-dirs videos \
  --test-profile minimal \
  --iterations 1 \
  --dry-run
```

### 2. 并发能力测试
```bash
# 测试8并发处理能力
python benchmark/concurrent_stress_test.py \
  --video-dirs videos \
  --max-workers 8 \
  --iterations 3 \
  --test-type concurrent
```

### 3. 持续负载测试
```bash
# 30分钟持续负载，目标5QPS
python benchmark/cloud_stress_test.py \
  --video-dirs /data/videos \
  --test-mode sustained \
  --duration 30 \
  --target-qps 5.0
```

### 4. 极限压力测试
```bash
# 64并发极限测试
python benchmark/cloud_stress_test.py \
  --video-dirs /data/videos \
  --test-profile stress \
  --max-workers 64 \
  --iterations 10
```

### 5. 综合测试
```bash
# 并发+持续组合测试
python benchmark/cloud_stress_test.py \
  --video-dirs /data/videos \
  --test-mode both \
  --test-profile comprehensive \
  --duration 60 \
  --iterations 5
```

## 📊 结果分析

### 自动生成报告
- **JSON格式**: 详细的测试数据和系统信息
- **CSV格式**: 便于Excel分析的数据表
- **汇总报告**: 包含性能统计和系统资源使用

### 关键指标解读
- **成功率**: 应保持在95%以上
- **执行时间**: 关注平均值和标准差
- **内存使用**: 监控增长趋势，防止内存泄漏
- **CPU使用率**: 验证资源利用效率
- **吞吐量**: QPS和帧处理速度

### 性能优化建议
1. **内存优化**: 降低分辨率，减少K值
2. **CPU优化**: 调整并发数为CPU核心数×1.5
3. **I/O优化**: 使用本地SSD存储，避免网络文件系统

## 🐛 故障排除

### 常见问题

#### 1. 内存不足 (OOM)
```bash
# 减少并发数和降低配置
python benchmark/cloud_stress_test.py \
  --video-dirs videos \
  --max-workers 2 \
  --test-profile minimal
```

#### 2. 权限错误
```bash
chmod +x *.sh
chmod -R 755 videos/
```

#### 3. 依赖缺失
```bash
pip install opencv-python psutil pandas matplotlib
```

### 性能问题诊断
```bash
# 检查系统资源
htop
iotop
netstat -i

# 检查磁盘空间
df -h

# 检查内存使用
free -h
```

## 📞 技术支持

### 调试信息收集
当遇到问题时，请提供：
1. 系统配置信息
2. 错误日志文件 (`logs/stress_test_*.log`)
3. 使用的命令和参数
4. 视频文件信息（格式、大小、时长）

### 性能优化咨询
根据测试结果，可以提供针对性的性能优化建议：
- 硬件配置优化
- 参数调优建议
- 架构改进方案

## 🎯 后续计划

1. **GPU加速支持**: 集成CUDA加速视频处理
2. **分布式测试**: 支持多机器协同压力测试
3. **实时监控面板**: Web界面实时查看测试状态
4. **性能回归检测**: 自动检测性能退化
5. **云原生部署**: Docker容器化和Kubernetes支持

---

**注意**: 本测试套件设计为生产级工具，建议在正式环境部署前充分测试和验证。
