# 安装指南

## 🎯 概述

本指南提供了知识库召回测试与翻译平台的详细安装步骤、依赖管理和故障排除方案。

## 📋 系统要求

### 基础要求
- **Python**: 3.8 或更高版本
- **操作系统**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **内存**: 最低 4GB RAM（推荐 8GB+）
- **存储**: 至少 2GB 可用空间

### 可选要求
- **GPU**: 支持CUDA的显卡（用于本地AI模型加速）
- **LibreOffice**: 用于文档格式转换

## 🚀 快速安装

### 方法1：使用安装脚本（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd kb

# 运行安装脚本
bash install.sh

# 快速启动
python quick_start.py
```

### 方法2：手动安装

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. 升级pip
pip install --upgrade pip

# 4. 安装依赖
pip install -r requirements.txt

# 5. 验证安装
python main.py --help
```

## 📦 依赖包详解

### 核心依赖

```txt
# HTTP和网络
requests>=2.28.0          # API请求库

# Web框架
Flask==2.3.3              # Web服务器
Flask-CORS==4.0.0          # 跨域支持
werkzeug==2.3.7           # WSGI工具包
markupsafe==2.1.3         # 模板安全

# 数据处理
numpy>=1.21.0             # 数值计算
pandas==2.0.3             # 数据分析

# 文档处理
pdf2docx==0.5.6           # PDF转换
python-docx==0.8.11       # Word文档
PyPDF2==3.0.1             # PDF处理
reportlab==4.0.7          # PDF生成
python-pptx==1.0.2        # PowerPoint
Pillow>=9.0.0             # 图像处理

# AI/ML库
transformers==4.35.2      # 机器学习模型
torch==2.1.1              # 深度学习框架
sentencepiece==0.1.99     # 文本分词
sacremoses==0.0.53        # 文本预处理
openai==1.3.5             # OpenAI API

# 工具库
python-dotenv==1.0.0      # 环境变量管理
```

### 可选依赖

```bash
# Web界面功能
pip install streamlit plotly matplotlib seaborn

# 开发和测试
pip install pytest openpyxl

# 高级功能
pip install structlog cachetools psutil pydantic prometheus-client
```

## ⚙️ 配置设置

### 基础配置

1. **复制配置模板**
   ```bash
   cp examples/translation_config_complete.json config/translation_config.json
   ```

2. **编辑主配置文件**
   ```json
   {
     "api": {
       "url": "https://api.dify.ai",
       "key": "your_api_key_here",
       "dataset_id": "your_dataset_id"
     },
     "testing": {
       "top_k": 5,
       "score_threshold": 0.7,
       "delay_between_requests": 1.0
     }
   }
   ```

3. **设置翻译配置**
   ```json
   {
     "translation": {
       "default_engine": "openai",
       "engines": {
         "openai": {
           "api_key": "your_openai_key",
           "model": "gpt-3.5-turbo"
         }
       }
     }
   }
   ```

### 环境变量配置

创建 `.env` 文件：

```bash
# API配置
DIFY_API_KEY=your_dify_api_key
DIFY_API_URL=https://api.dify.ai
DIFY_DATASET_ID=your_dataset_id

# OpenAI配置
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1

# DeepSeek配置
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 其他配置
LOG_LEVEL=INFO
DEBUG=False
```

## ✅ 安装验证

### 基础功能测试

```bash
# 1. 检查主程序
python main.py --version

# 2. 测试API连接
python main.py test-connection

# 3. 运行示例测试
python main.py basic-test --test-file examples/test_cases_sample.csv

# 4. 启动Web界面
python web_interface.py
```

### 翻译功能测试

```bash
# 测试NLLB本地翻译
python tools/download_nllb_model.py

# 测试文档翻译
python main.py translate --input test.pdf --output translated.pdf --source zh --target en
```

## 🔧 故障排除

### 常见安装问题

#### 1. Python版本不兼容

**问题**: `SyntaxError` 或版本警告

**解决方案**:
```bash
# 检查Python版本
python --version

# 如果版本过低，升级Python
# Windows: 从官网下载最新版本
# macOS: brew install python@3.9
# Ubuntu: sudo apt update && sudo apt install python3.9
```

#### 2. pip安装失败

**问题**: `pip install` 命令失败

**解决方案**:
```bash
# 升级pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 如果仍然失败，尝试单独安装
pip install requests flask numpy pandas
```

#### 3. 依赖包冲突

**问题**: 包版本冲突或依赖解析失败

**解决方案**:
```bash
# 创建新的虚拟环境
python -m venv fresh_env
source fresh_env/bin/activate  # Linux/macOS
# 或 fresh_env\Scripts\activate  # Windows

# 清理pip缓存
pip cache purge

# 重新安装
pip install -r requirements.txt
```

#### 4. Streamlit安装失败

**问题**: `streamlit` 或 `pyarrow` 编译失败

**解决方案**:
```bash
# 方案1: 使用conda安装
conda install streamlit

# 方案2: 跳过Web界面功能
# 注释掉requirements.txt中的streamlit相关包

# 方案3: 使用预编译版本
pip install streamlit --no-build-isolation
```

#### 5. PyTorch安装问题

**问题**: `torch` 安装缓慢或失败

**解决方案**:
```bash
# CPU版本（更小更快）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# GPU版本（如果有CUDA）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 运行时问题

#### 1. API连接失败

**问题**: 无法连接到Dify API

**解决方案**:
```bash
# 检查网络连接
curl -I https://api.dify.ai

# 验证API密钥
python -c "import requests; print(requests.get('https://api.dify.ai/v1/datasets', headers={'Authorization': 'Bearer YOUR_KEY'}).status_code)"

# 检查防火墙设置
```

#### 2. 文件权限问题

**问题**: 无法读写文件

**解决方案**:
```bash
# Linux/macOS
chmod +x install.sh
chmod -R 755 data/
chmod -R 755 uploads/

# Windows
# 右键 -> 属性 -> 安全 -> 编辑权限
```

#### 3. 内存不足

**问题**: 处理大文件时内存溢出

**解决方案**:
```python
# 在config.json中调整设置
{
  "processing": {
    "chunk_size": 500,  # 减小块大小
    "batch_size": 5,    # 减小批处理大小
    "max_workers": 2    # 减少并发数
  }
}
```

## 🔄 更新和维护

### 更新项目

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 运行数据库迁移（如果需要）
python tools/migrate_to_unified_db.py
```

### 清理和重置

```bash
# 清理缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# 重置数据库
rm -rf data/*.db
python main.py init-db

# 重置配置
cp examples/translation_config_complete.json config/translation_config.json
```

## 📊 性能优化

### 系统优化

```bash
# 1. 增加文件描述符限制
ulimit -n 4096

# 2. 设置环境变量
export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false

# 3. 优化Python垃圾回收
export PYTHONGC=1
```

### 配置优化

```json
{
  "performance": {
    "enable_caching": true,
    "cache_size": 1000,
    "parallel_processing": true,
    "max_workers": 4,
    "memory_limit": "2GB"
  }
}
```

## 🐳 Docker部署

### Dockerfile示例

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p data uploads logs

# 设置权限
RUN chmod +x install.sh

# 暴露端口
EXPOSE 5000 8501

# 启动命令
CMD ["python", "main.py", "web"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  kb-app:
    build: .
    ports:
      - "5000:5000"
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./config:/app/config
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

## 📞 获取帮助

### 自助诊断

```bash
# 运行诊断脚本
python main.py diagnose

# 查看日志
tail -f logs/app.log

# 检查系统状态
python main.py status
```

### 社区支持

- **文档**: 查看 `docs/` 目录下的详细文档
- **示例**: 参考 `examples/` 目录下的配置示例
- **测试**: 运行 `pytest` 查看测试结果

### 报告问题

提交Issue时请包含：

1. **系统信息**
   ```bash
   python --version
   pip list
   uname -a  # Linux/macOS
   ```

2. **错误日志**
   ```bash
   # 完整的错误堆栈信息
   python main.py --debug
   ```

3. **配置信息**（隐藏敏感信息）
   ```json
   {
     "api": {
       "url": "https://api.dify.ai",
       "key": "sk-***"
     }
   }
   ```

---

*安装过程中遇到问题？查看故障排除部分或提交Issue获取帮助！*