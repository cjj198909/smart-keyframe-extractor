# Azure Blob Storage 认证方式支持

## 🔐 当前支持的认证方式

Smart Keyframe Extractor 通过 `DefaultAzureCredential` 支持多种Azure认证方式，按优先级顺序自动尝试：

### 1. Azure CLI 认证 ✅ (已验证)
**推荐方式**，适用于开发和测试环境

```bash
# 安装Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# 登录Azure
az login

# 验证登录状态
az account show
```

**优点**：
- ✅ 简单易用，一次登录持久有效
- ✅ 支持多租户和多订阅
- ✅ 自动刷新token
- ✅ 本地开发友好

### 2. 环境变量认证 ✅
适用于CI/CD和容器化环境

```bash
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret" 
export AZURE_TENANT_ID="your-tenant-id"
```

**或使用证书**：
```bash
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_CERTIFICATE_PATH="/path/to/cert.pem"
export AZURE_TENANT_ID="your-tenant-id"
```

### 3. 托管身份认证 ✅
适用于Azure虚拟机、容器实例、函数应用等

**系统分配的托管身份**：
- 在Azure资源上自动启用
- 无需配置，自动获取token

**用户分配的托管身份**：
```bash
export AZURE_CLIENT_ID="user-assigned-identity-client-id"
```

### 4. Visual Studio Code 认证 ✅
适用于VS Code开发环境

- 通过Azure扩展登录
- 自动使用VS Code的认证token

### 5. Azure PowerShell 认证 ✅
适用于PowerShell环境

```powershell
Connect-AzAccount
```

### 6. 工作站认证 ✅
适用于加入Azure AD域的工作站

- 使用当前Windows用户的Kerberos ticket
- 无需额外配置

## 🚀 使用示例

### 开发环境快速开始
```bash
# 1. 安装依赖
pip install smart-keyframe-extractor[remote]

# 2. Azure CLI登录
az login

# 3. 处理视频
python -c "
from smart_keyframe_extractor.extractor import extract_top_k_keyframes
results = extract_top_k_keyframes(
    'https://yourstorage.blob.core.windows.net/container/video.mp4',
    k=5,
    save_files=True
)
"
```

### 生产环境部署
```bash
# 使用服务主体认证
export AZURE_CLIENT_ID="app-id"
export AZURE_CLIENT_SECRET="app-secret"
export AZURE_TENANT_ID="tenant-id"

# 运行应用
python your_app.py
```

### Docker容器部署
```dockerfile
FROM python:3.11

# 安装依赖
RUN pip install smart-keyframe-extractor[remote]

# 设置环境变量
ENV AZURE_CLIENT_ID=your-client-id
ENV AZURE_CLIENT_SECRET=your-client-secret
ENV AZURE_TENANT_ID=your-tenant-id

# 运行应用
CMD ["python", "app.py"]
```

### Azure Functions部署
```python
import os
from smart_keyframe_extractor.extractor import extract_top_k_keyframes

def main(req):
    # 使用托管身份，无需配置
    video_url = req.params.get('video_url')
    results = extract_top_k_keyframes(video_url, k=3)
    return results
```

## 🔧 认证配置详解

### DefaultAzureCredential 认证链
```python
from azure.identity import DefaultAzureCredential

# 自动按顺序尝试以下认证方式：
credential = DefaultAzureCredential()

# 认证顺序：
# 1. 环境变量 (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)
# 2. 托管身份 (Azure VM, Container Instance, Function App等)
# 3. Azure CLI (az login)
# 4. Azure PowerShell (Connect-AzAccount)  
# 5. Visual Studio Code
# 6. 工作站认证 (域用户)
```

### 自定义认证方式
如需特定认证方式，可以修改代码：

```python
from azure.identity import (
    ClientSecretCredential,
    ClientCertificateCredential,
    ManagedIdentityCredential,
    AzureCliCredential
)

# 使用特定认证
credential = AzureCliCredential()  # 仅使用Azure CLI
# 或
credential = ManagedIdentityCredential()  # 仅使用托管身份
# 或  
credential = ClientSecretCredential(
    tenant_id="your-tenant",
    client_id="your-client-id", 
    client_secret="your-secret"
)
```

## 🛡️ 安全最佳实践

### 1. 权限最小化
为存储账户分配最小必要权限：

```bash
# 创建自定义角色（仅读取blob）
az role definition create --role-definition '{
    "Name": "Blob Reader",
    "Description": "Read access to blob storage",
    "Actions": [
        "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"
    ],
    "AssignableScopes": ["/subscriptions/your-subscription-id"]
}'

# 分配角色
az role assignment create \
    --assignee your-app-id \
    --role "Blob Reader" \
    --scope /subscriptions/your-subscription-id/resourceGroups/your-rg/providers/Microsoft.Storage/storageAccounts/your-storage
```

### 2. 密钥管理
生产环境使用Azure Key Vault：

```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://your-keyvault.vault.azure.net/",
    credential=credential
)

# 获取密钥
secret = client.get_secret("storage-connection-string")
```

### 3. 网络安全
配置存储账户网络访问：

```bash
# 限制网络访问
az storage account update \
    --name yourstorage \
    --resource-group your-rg \
    --default-action Deny

# 添加允许的IP范围
az storage account network-rule add \
    --account-name yourstorage \
    --resource-group your-rg \
    --ip-address 203.0.113.0/24
```

## 📊 认证方式对比

| 认证方式 | 适用场景 | 安全性 | 易用性 | 维护成本 |
|----------|----------|--------|--------|----------|
| **Azure CLI** | 开发/测试 | 🟢 高 | 🟢 高 | 🟢 低 |
| **环境变量** | CI/CD | 🟡 中 | 🟢 高 | 🟡 中 |
| **托管身份** | Azure资源 | 🟢 高 | 🟢 高 | 🟢 低 |
| **服务主体** | 企业应用 | 🟢 高 | 🟡 中 | 🟡 中 |
| **证书认证** | 高安全需求 | 🟢 高 | 🔴 低 | 🔴 高 |

## 🔍 故障排除

### 常见问题和解决方案

#### 1. 认证失败 (401 Unauthorized)
```bash
# 检查Azure CLI登录状态
az account show

# 重新登录
az logout
az login

# 检查订阅权限
az role assignment list --assignee $(az account show --query user.name -o tsv)
```

#### 2. 权限不足 (403 Forbidden)
```bash
# 检查存储账户权限
az role assignment list \
    --scope /subscriptions/your-subscription/resourceGroups/your-rg/providers/Microsoft.Storage/storageAccounts/your-storage

# 分配存储Blob数据读取者角色
az role assignment create \
    --assignee $(az account show --query user.name -o tsv) \
    --role "Storage Blob Data Reader" \
    --scope /subscriptions/your-subscription/resourceGroups/your-rg/providers/Microsoft.Storage/storageAccounts/your-storage
```

#### 3. 网络访问被拒绝
```bash
# 检查存储账户网络规则
az storage account show \
    --name yourstorage \
    --resource-group your-rg \
    --query networkRuleSet

# 临时允许所有网络访问（仅测试用）
az storage account update \
    --name yourstorage \
    --resource-group your-rg \
    --default-action Allow
```

#### 4. 调试认证过程
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 启用详细日志
from smart_keyframe_extractor.extractor import extract_top_k_keyframes
results = extract_top_k_keyframes('https://storage.blob.core.windows.net/container/video.mp4')
```

## 📚 相关文档

- [Azure Identity 库文档](https://docs.microsoft.com/en-us/python/api/azure-identity/)
- [Azure CLI 认证](https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli)
- [Azure 托管身份](https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/)
- [Azure Blob Storage 权限](https://docs.microsoft.com/en-us/azure/storage/blobs/security-recommendations)

---

**💡 推荐配置**: 开发环境使用Azure CLI，生产环境使用托管身份或服务主体
