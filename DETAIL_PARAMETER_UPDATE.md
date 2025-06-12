# Azure OpenAI Detail 参数功能更新

## 🆕 新增功能

在 Azure OpenAI 分析模块中添加了 `detail` 参数，允许用户控制图像分析的精度和token消耗。

## 📋 功能详情

### 新增参数

- **参数名**: `detail`
- **类型**: `str`
- **默认值**: `"high"`
- **可选值**: `"low"`, `"high"`, `"auto"`

### 影响的方法

1. **`AzureOpenAIAnalyzer.analyze_video_frames()`**
   ```python
   def analyze_video_frames(self, 
                          frames: List[Dict], 
                          custom_prompt: str = None,
                          max_tokens: int = 1000,
                          temperature: float = 0.7,
                          detail: str = "high") -> Dict:
   ```

2. **`analyze_video_with_azure_openai()`**
   ```python
   def analyze_video_with_azure_openai(video_path: str,
                                      api_key: str = None,
                                      endpoint: str = None,
                                      k: Union[int, str] = 5,
                                      resolution: str = '720p',
                                      custom_prompt: str = None,
                                      detail: str = "high",
                                      **extract_kwargs) -> Dict:
   ```

3. **`_prepare_messages()`** (内部方法)
   - 添加了 detail 参数验证
   - 自动处理无效参数，回退到默认值

## 🎯 使用场景

### High Detail (`detail="high"`)
- **适用场景**: 需要精确识别和详细分析
- **特点**: 高精度，更多细节，消耗更多tokens
- **用例**: 内容审核、精细分析、重要场景识别

### Low Detail (`detail="low"`)  
- **适用场景**: 批量处理、快速预览
- **特点**: 快速分析，消耗较少tokens
- **用例**: 大规模视频处理、成本敏感的应用

### Auto Detail (`detail="auto"`)
- **适用场景**: 不确定最佳策略时
- **特点**: 系统自动选择最佳模式
- **用例**: 混合场景、智能优化

## 💻 代码示例

### 基础使用
```python
from smart_keyframe_extractor.azure_openai import AzureOpenAIAnalyzer

analyzer = AzureOpenAIAnalyzer()

# 高精度分析
result_high = analyzer.analyze_video_frames(
    frames=frames,
    detail="high"
)

# 快速分析
result_low = analyzer.analyze_video_frames(
    frames=frames,
    detail="low"
)
```

### 完整工作流
```python
from smart_keyframe_extractor.azure_openai import analyze_video_with_azure_openai

# 使用低精度进行快速批量处理
result = analyze_video_with_azure_openai(
    video_path="video.mp4",
    k=3,
    detail="low",
    custom_prompt="快速识别主要内容"
)
```

## 🔧 技术实现

### 参数验证
```python
valid_details = ["low", "high", "auto"]
if detail not in valid_details:
    logger.warning(f"无效的detail参数: {detail}，使用默认值 'high'")
    detail = "high"
```

### 消息格式
```python
content.append({
    "type": "image_url",
    "image_url": {
        "url": f"data:image/jpeg;base64,{frame['base64']}",
        "detail": detail  # 动态设置detail参数
    }
})
```

## 📊 性能影响

| Detail模式 | Token消耗 | 分析速度 | 分析精度 | 适用场景 |
|-----------|----------|----------|----------|----------|
| low       | 较少     | 较快     | 基础     | 批量处理 |
| high      | 较多     | 较慢     | 精细     | 详细分析 |
| auto      | 自适应   | 平衡     | 智能     | 通用场景 |

## 🧪 测试验证

已添加测试文件验证功能：
- `test_detail_simple.py`: 基础功能测试
- `examples/detail_parameter_example.py`: 完整使用示例

## 🔄 向后兼容性

- 默认值为 `"high"`，保持原有行为不变
- 现有代码无需修改即可继续使用
- 新参数为可选参数，完全向后兼容

## 📝 文档更新

- 更新了 `README.md` 添加detail参数说明
- 添加了使用示例和最佳实践建议
- 更新了方法文档字符串

---

## ✅ 功能状态

**状态**: ✅ 已完成  
**版本**: 0.1.1  
**兼容性**: 向后兼容  
**测试**: 已验证  

这个功能增强了 Azure OpenAI 集成的灵活性，让用户可以根据具体需求优化分析精度和成本。
