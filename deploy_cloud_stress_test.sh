#!/bin/bash

# Smart Keyframe Extractor - 云服务器压力测试部署脚本
# 适用于 Ubuntu/CentOS 云服务器

echo "🚀 Smart Keyframe Extractor - 云服务器压力测试部署"
echo "=================================================="

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | cut -d" " -f2)
echo "🐍 Python 版本: $python_version"

# 安装系统依赖
echo "📦 安装系统依赖..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv ffmpeg libopencv-dev
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum update -y
    sudo yum install -y python3-pip python3-venv ffmpeg opencv-devel
    # 如果 ffmpeg 不在默认仓库，尝试 EPEL
    sudo yum install -y epel-release
    sudo yum install -y ffmpeg
fi

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
python3 -m venv stress_test_env
source stress_test_env/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装 Python 依赖
echo "📚 安装 Python 依赖..."
pip install opencv-python
pip install psutil
pip install pandas
pip install matplotlib
pip install concurrent-futures

# 创建测试目录结构
echo "📁 创建目录结构..."
mkdir -p {videos,benchmark_results,cloud_stress_results,logs}

# 创建配置文件
echo "⚙️ 创建配置文件..."
cat > cloud_test_config.json << EOF
{
  "minimal": [
    {"name": "minimal_test", "k": 3, "resolution": "480p"}
  ],
  "standard": [
    {"name": "standard_low", "k": 5, "resolution": "720p"},
    {"name": "standard_high", "k": 5, "resolution": "original"}
  ],
  "comprehensive": [
    {"name": "ultra_fast", "k": 3, "resolution": "480p"},
    {"name": "fast", "k": 5, "resolution": "720p"},
    {"name": "balanced", "k": 5, "resolution": "720p"},
    {"name": "high_quality", "k": 10, "resolution": "original"},
    {"name": "max_quality", "k": 15, "resolution": "original"}
  ],
  "stress": [
    {"name": "stress_1", "k": 5, "resolution": "original"},
    {"name": "stress_2", "k": 10, "resolution": "original"},
    {"name": "stress_3", "k": 15, "resolution": "original"},
    {"name": "stress_4", "k": 20, "resolution": "original"}
  ]
}
EOF

# 创建快速启动脚本
cat > run_stress_test.sh << 'EOF'
#!/bin/bash

# 激活虚拟环境
source stress_test_env/bin/activate

# 设置日志文件
LOG_FILE="logs/stress_test_$(date +%Y%m%d_%H%M%S).log"

echo "🚀 启动压力测试..."
echo "📄 日志文件: $LOG_FILE"

# 检查参数
if [ $# -eq 0 ]; then
    echo "❌ 请提供视频目录参数"
    echo "用法示例:"
    echo "  ./run_stress_test.sh /path/to/videos"
    echo "  ./run_stress_test.sh /path/to/videos --test-profile comprehensive"
    echo "  ./run_stress_test.sh /path/to/videos --test-mode both --duration 60"
    exit 1
fi

# 运行压力测试
python3 benchmark/cloud_stress_test.py --video-dirs "$@" 2>&1 | tee "$LOG_FILE"

echo "✅ 测试完成，日志已保存到: $LOG_FILE"
EOF

chmod +x run_stress_test.sh

# 创建系统资源监控脚本
cat > monitor_system.sh << 'EOF'
#!/bin/bash

# 系统资源监控脚本
# 在压力测试期间运行此脚本来监控系统状态

LOG_FILE="logs/system_monitor_$(date +%Y%m%d_%H%M%S).log"
INTERVAL=5  # 监控间隔（秒）

echo "📊 开始监控系统资源..." | tee "$LOG_FILE"
echo "⏱️ 监控间隔: ${INTERVAL}秒" | tee -a "$LOG_FILE"
echo "📄 日志文件: $LOG_FILE" | tee -a "$LOG_FILE"
echo "按 Ctrl+C 停止监控" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 监控循环
while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # CPU 使用率
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    
    # 内存使用率
    memory_info=$(free | grep Mem)
    memory_total=$(echo $memory_info | awk '{print $2}')
    memory_used=$(echo $memory_info | awk '{print $3}')
    memory_percent=$(awk "BEGIN {printf \"%.1f\", $memory_used/$memory_total*100}")
    
    # 磁盘使用率
    disk_usage=$(df -h / | awk 'NR==2{print $5}')
    
    # 负载平均值
    load_avg=$(uptime | awk -F'load average:' '{print $2}')
    
    # 网络连接数
    connections=$(ss -t state established | wc -l)
    
    echo "[$timestamp] CPU: ${cpu_usage}% | 内存: ${memory_percent}% | 磁盘: ${disk_usage} | 负载: ${load_avg} | 连接: ${connections}" | tee -a "$LOG_FILE"
    
    sleep $INTERVAL
done
EOF

chmod +x monitor_system.sh

# 创建结果分析脚本
cat > analyze_results.py << 'EOF'
#!/usr/bin/env python3
"""
结果分析脚本 - 分析压力测试结果
"""

import json
import glob
import pandas as pd
import sys
from pathlib import Path

def analyze_all_results():
    """分析所有测试结果"""
    
    # 查找所有结果文件
    result_files = glob.glob("cloud_stress_results/*.json")
    
    if not result_files:
        print("❌ 未找到测试结果文件")
        return
    
    print(f"📊 找到 {len(result_files)} 个结果文件")
    
    all_results = []
    for file_path in result_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'results' in data:
                    all_results.extend(data['results'])
        except Exception as e:
            print(f"⚠️ 无法读取文件 {file_path}: {e}")
    
    if not all_results:
        print("❌ 没有有效的测试结果")
        return
    
    # 转换为 DataFrame
    df = pd.DataFrame(all_results)
    
    print(f"\n📈 总体统计:")
    print(f"   总任务数: {len(df)}")
    print(f"   成功任务: {df['success'].sum()}")
    print(f"   成功率: {df['success'].mean()*100:.1f}%")
    print(f"   平均执行时间: {df[df['success']]['execution_time'].mean():.2f}s")
    print(f"   平均内存使用: {df[df['success']]['memory_usage'].mean():.1f}MB")
    
    # 按配置分组统计
    print(f"\n📊 按配置分组统计:")
    config_stats = df.groupby(df['config'].astype(str)).agg({
        'success': ['count', 'sum', 'mean'],
        'execution_time': ['mean', 'std'],
        'memory_usage': ['mean', 'std'],
        'keyframes_extracted': 'mean'
    }).round(2)
    
    print(config_stats)
    
    # 保存分析结果
    output_file = f"analysis_summary_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
    config_stats.to_csv(output_file)
    print(f"\n💾 分析结果已保存到: {output_file}")

if __name__ == "__main__":
    analyze_all_results()
EOF

chmod +x analyze_results.py

# 创建README文件
cat > CLOUD_STRESS_TEST_README.md << 'EOF'
# Smart Keyframe Extractor - 云服务器压力测试

## 🚀 快速开始

### 1. 上传视频文件
将你的视频文件上传到服务器的某个目录，例如：
```bash
mkdir /data/videos
# 上传视频文件到 /data/videos
```

### 2. 运行基础压力测试
```bash
./run_stress_test.sh /data/videos
```

### 3. 运行全面压力测试
```bash
./run_stress_test.sh /data/videos --test-profile comprehensive --iterations 3
```

### 4. 运行持续负载测试
```bash
./run_stress_test.sh /data/videos --test-mode sustained --duration 60 --target-qps 5.0
```

## 📊 测试配置档案

- **minimal**: 最小测试配置，快速验证
- **standard**: 标准测试配置，适合一般性能测试
- **comprehensive**: 全面测试配置，包含多种场景
- **stress**: 压力测试配置，高负载测试

## 🔧 高级用法

### 自定义并发数
```bash
./run_stress_test.sh /data/videos --max-workers 16
```

### 使用自定义配置
```bash
./run_stress_test.sh /data/videos --custom-config custom_config.json
```

### 并发+持续组合测试
```bash
./run_stress_test.sh /data/videos --test-mode both --duration 30
```

## 📈 监控系统资源

在另一个终端运行系统监控：
```bash
./monitor_system.sh
```

## 📊 分析测试结果

```bash
python3 analyze_results.py
```

## 📁 目录结构

```
├── videos/                 # 测试视频目录
├── cloud_stress_results/   # 测试结果输出
├── logs/                   # 日志文件
├── run_stress_test.sh      # 快速启动脚本
├── monitor_system.sh       # 系统监控脚本
└── analyze_results.py      # 结果分析脚本
```

## 🐛 故障排除

### 1. 内存不足
- 减少并发数: `--max-workers 4`
- 使用低分辨率配置: `--test-profile minimal`

### 2. 视频文件格式问题
- 检查视频文件完整性
- 确保 FFmpeg 支持该格式

### 3. 权限问题
- 确保脚本有执行权限: `chmod +x *.sh`
- 检查视频目录读取权限

## 📞 技术支持

如有问题，请查看日志文件：
- 测试日志: `logs/stress_test_*.log`
- 系统监控日志: `logs/system_monitor_*.log`
EOF

echo ""
echo "✅ 云服务器压力测试环境部署完成!"
echo ""
echo "📋 接下来的步骤:"
echo "1. 上传视频文件到服务器"
echo "2. 运行 ./run_stress_test.sh /path/to/videos"
echo "3. 查看 CLOUD_STRESS_TEST_README.md 了解详细用法"
echo ""
echo "🔗 示例命令:"
echo "  ./run_stress_test.sh /data/videos --test-profile standard"
echo "  ./monitor_system.sh  # 在另一个终端运行"
echo ""
