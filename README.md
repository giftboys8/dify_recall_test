# 知识管理平台 (Knowledge Management Platform)

一个集成了知识库召回测试、PDF文档翻译、创意收集、在线学习和网站收藏等功能的综合知识管理平台。

## 项目结构

```
/opt/work/kb/
├── src/                             # 源代码目录
│   ├── core/                        # 核心功能
│   │   ├── __init__.py
│   │   ├── tester.py                # 主测试引擎
│   │   └── basic_tester.py          # 基础测试脚本
│   ├── utils/                       # 工具函数
│   │   └── __init__.py
│   └── api/                         # API接口
│       ├── __init__.py
│       └── web_server.py            # Web服务器
├── config/                          # 配置文件目录
│   ├── default.json                 # 默认配置
│   └── template.json                # 配置模板
├── tests/                           # 测试目录
│   ├── unit/                        # 单元测试
│   ├── integration/                 # 集成测试
│   └── test_cases/                  # 测试用例
│       └── sample.csv               # 示例测试用例
├── data/                            # 数据目录
│   ├── input/                       # 输入数据
│   └── output/                      # 输出数据
│       ├── results/                 # 测试结果
│       └── dify_recall_test.log     # 日志文件
├── scripts/                         # 脚本目录
│   ├── install.sh                   # 安装脚本
│   └── quick_start.py               # 快速启动
├── docs/                            # 文档目录
│   ├── api/                         # API文档
│   ├── user/                        # 用户文档
│   └── dev/                         # 开发文档
├── main.py                          # 主入口文件
├── setup.py                         # 包安装配置
├── Makefile                         # 构建脚本
├── pytest.ini                      # 测试配置
├── requirements.txt                 # 依赖管理
└── README.md                        # 项目文档
```

## 🚀 功能特性

### 🔍 召回测试 (Recall Testing)
- **批量测试**: 支持从CSV文件批量导入测试用例
- **详细分析**: 获取每个查询的详细召回结果和分数
- **多种输出格式**: 支持CSV、JSON格式的结果导出
- **可视化分析**: 生成分数分布、分类统计等图表
- **配置灵活**: 支持配置文件和命令行参数
- **实时监控**: 提供测试进度和结果的实时反馈

### 📄 PDF文档转换 (PDF Translation)
- **多语言支持**: 支持中英日韩法德西等多种语言互译
- **多种翻译引擎**: 支持NLLB本地模型、OpenAI和DeepSeek API翻译
- **智能布局**: 提供并排对照和段落对段落两种布局模式
- **格式保持**: 保持原文档的格式和结构
- **批量处理**: 支持单个或批量PDF文件翻译
- **多种输出**: 支持DOCX、PDF或双格式输出
- **翻译历史**: 记录翻译历史和下载管理
- **离线支持**: NLLB模型支持离线使用，无需网络连接

### 💡 创意收集 (Ideas Collection)
- **灵感记录**: 快速记录和整理创意想法
- **分类管理**: 支持多级分类和标签系统
- **搜索功能**: 强大的全文搜索和筛选功能
- **多种视图**: 支持表格、卡片和看板视图
- **导入导出**: 支持数据的导入导出功能

### 📚 在线学习 (Document Learning)
- **文档查看**: 支持PDF文档的在线阅读
- **智能标注**: 提供高亮、注释和笔记功能
- **学习进度**: 跟踪学习进度和时间统计
- **页面导航**: 便捷的页面缩略图导航
- **笔记管理**: 集中管理所有学习笔记

### 🌐 网站收藏 (Website Bookmarks)
- **网站管理**: 收藏和管理常用网站
- **智能分类**: 支持标签和分类系统
- **语义搜索**: 基于内容的智能搜索功能
- **访问统计**: 记录网站访问次数和时间
- **数据同步**: 支持书签数据的导入导出

### 🎯 统一导航系统
- **现代化界面**: 采用响应式设计和现代UI风格
- **统一导航**: 所有功能模块通过统一导航访问
- **快速切换**: 在不同功能模块间快速切换
- **状态保持**: 保持用户的操作状态和偏好设置

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用安装脚本
bash scripts/install.sh

# 或者使用Makefile
make install

# 开发环境安装
make install-dev
```

### 2. 配置文件

复制配置模板并修改：

```bash
cp config/template.json config/default.json
```

编辑 `config/default.json` 文件，填入您的Dify API信息：

```json
{
  "api_base_url": "http://your-dify-instance.com/",
  "api_key": "your-api-key",
  "dataset_id": "your-dataset-id"
}
```

### 3. 准备测试用例

编辑 `tests/test_cases/sample.csv` 文件，添加您的测试查询：

```csv
id,query,category
1,如何配置数据库连接,技术问题
2,用户登录失败怎么办,故障排查
```

### 4. 运行测试

#### 使用主入口（推荐）

```bash
# 运行完整测试
python main.py test --config config/default.json --test-file tests/test_cases/sample.csv --generate-viz

# 或使用Makefile
make run-test
```

#### 启动Web界面

```bash
# 启动Web服务器
python main.py web --port 8080

# 或使用Makefile
make run-web
```

访问 http://localhost:8080 即可使用Web界面，包含：
- **首页**: 功能模块导航和平台概览
- **召回测试**: 知识库召回测试功能
- **PDF文档转换**: PDF翻译功能
- **创意收集**: 想法和创意管理
- **在线学习**: 文档阅读和学习笔记
- **网站收藏**: 网站书签管理

#### NLLB模型预下载（可选）

如果您计划在离线环境下使用NLLB翻译功能，建议预先下载模型：

```bash
# 下载默认NLLB模型到本地缓存
python download_nllb_model.py

# 或下载指定模型
python download_nllb_model.py facebook/nllb-200-distilled-1.3B
```

下载完成后，系统会自动优先使用本地缓存的模型，无需网络连接。

#### 快速启动

```bash
# 快速开始
python main.py quick-start

# 或使用Makefile
make quick-test
```

## 🌟 平台特色

### 集成化设计
知识管理平台将多个常用的知识工作流程集成在一个统一的界面中，包括：
- 知识库质量测试
- 文档翻译处理
- 创意想法收集
- 学习笔记管理
- 网站资源收藏

### 现代化界面
- 响应式设计，支持桌面和移动设备
- 直观的卡片式布局
- 统一的导航系统
- 现代化的UI组件

### 数据安全
- 本地数据存储
- 支持离线使用
- 数据导入导出功能
- 隐私保护设计

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

## 🛠️ 使用方法

### 方法1: 命令行工具（基础版）

```bash
python dify_kb_recall_test.py \
  --api-url "https://api.dify.ai" \
  --api-key "your_api_key" \
  --dataset-id "your_dataset_id" \
  --test-file "test_cases_sample.csv" \
  --top-k 10 \
  --delay 1.0
```

### 方法2: 增强版命令行工具

#### 使用配置文件

1. 复制并编辑配置文件：
```bash
cp config_template.json config.json
# 编辑config.json，填入您的API信息
```

2. 运行测试：
```bash
python enhanced_recall_tester.py \
  --config config.json \
  --test-file test_cases_sample.csv \
  --output-dir ./results \
  --generate-viz
```

#### 直接使用命令行参数

```bash
python enhanced_recall_tester.py \
  --api-url "https://api.dify.ai" \
  --api-key "your_api_key" \
  --dataset-id "your_dataset_id" \
  --test-file test_cases_sample.csv \
  --output-dir ./results \
  --generate-viz
```

### 方法3: Web界面

启动Web界面：
```bash
python main.py web --port 8080
```

然后在浏览器中打开 http://localhost:8080

#### PDF翻译功能使用

1. **配置翻译设置**
   - 选择翻译提供商（NLLB本地模型或OpenAI）
   - 设置源语言和目标语言
   - 选择输出格式（DOCX、PDF或两者）
   - 选择布局模式（并排对照或段落对段落）

2. **测试翻译**
   - 在测试文本框中输入文本
   - 点击"Test Translation"验证翻译效果

3. **翻译PDF文件**
   - 上传PDF文件（最大50MB）
   - 点击"Translate PDF"开始翻译
   - 下载翻译结果

4. **查看翻译历史**
   - 查看所有翻译记录
   - 重新下载之前的翻译结果

## 📋 测试用例格式

测试用例CSV文件应包含以下列：

| 列名 | 描述 | 必需 |
|------|------|------|
| id | 测试用例唯一标识 | 是 |
| query | 查询文本 | 是 |
| category | 测试分类 | 否 |
| description | 测试描述 | 否 |
| expected_score_threshold | 期望的最低分数 | 否 |

### 示例CSV内容：

```csv
id,query,category,description
001,什么是人工智能？,基础概念,AI基础概念查询
002,机器学习的主要算法有哪些？,技术细节,ML算法查询
003,深度学习和传统机器学习的区别,对比分析,技术对比查询
```

## ⚙️ 配置说明

### config.json 配置文件格式：

```json
{
  "api_base_url": "https://api.dify.ai",
  "api_key": "your_api_key_here",
  "dataset_id": "your_dataset_id_here",
  "test_settings": {
    "top_k": 10,
    "delay_between_requests": 1.0,
    "score_threshold_enabled": false,
    "reranking_enabled": true,
    "reranking_model": {
      "provider": "cohere",
      "model": "rerank-multilingual-v3.0"
    }
  },
  "output_settings": {
    "save_csv": true,
    "save_detailed_json": true,
    "output_prefix": "recall_test",
    "include_document_content": true
  }
}
```

### 主要参数说明：

- `api_base_url`: Dify API的基础URL
- `api_key`: 您的Dify API密钥
- `dataset_id`: 要测试的知识库ID
- `top_k`: 每个查询返回的文档数量
- `delay_between_requests`: 请求之间的延迟时间（秒）
- `reranking_enabled`: 是否启用重排序
- `score_threshold_enabled`: 是否启用分数阈值过滤

## 📊 输出结果

### CSV结果文件包含：

- `test_id`: 测试用例ID
- `query`: 查询文本
- `category`: 测试分类
- `success`: 是否成功
- `response_time`: 响应时间
- `doc_count`: 召回文档数量
- `max_score`: 最高分数
- `min_score`: 最低分数
- `avg_score`: 平均分数
- `scores_json`: 所有分数的JSON数组
- `error_message`: 错误信息（如果失败）

### JSON详细结果包含：

- 完整的API响应数据
- 每个文档的详细信息
- 文档内容（可配置）
- 分段信息

### 分析报告包含：

- 总体统计信息
- 分数分布统计
- 按分类的性能分析
- 响应时间分析

## 📈 可视化图表

增强版工具可以生成以下图表：

1. **分数分布直方图**: 显示所有召回分数的分布情况
2. **分类平均分数**: 按测试分类显示平均召回分数
3. **响应时间分布**: 显示API响应时间的分布
4. **文档数量分布**: 显示每次查询召回的文档数量分布

## 🔧 高级用法

### 自定义重排序模型

在配置文件中修改重排序设置：

```json
"reranking_model": {
  "provider": "jina",
  "model": "jina-reranker-v2-base-multilingual"
}
```

支持的重排序提供商：
- `openai`: OpenAI重排序模型
- `cohere`: Cohere重排序模型  
- `jina`: Jina重排序模型（推荐使用 `jina-reranker-v2-base-multilingual`）


## 🌐 PDF翻译配置

### 支持的翻译提供商

#### NLLB本地模型（推荐）
- 无需API密钥
- 支持200+语言
- 本地处理，数据安全
- 模型：`facebook/nllb-200-distilled-600M`

#### OpenAI翻译
- 需要OpenAI API密钥
- 高质量翻译效果
- 支持主流语言
- 按使用量计费

#### DeepSeek翻译
- 需要DeepSeek API密钥
- 高性价比翻译服务
- 支持主流语言
- 兼容OpenAI API格式
- 模型：`deepseek-chat`

### 支持的语言

- **中文**: zh-CN (简体中文)
- **英语**: en (English)
- **日语**: ja (Japanese)
- **韩语**: ko (Korean)
- **法语**: fr (French)
- **德语**: de (German)
- **西班牙语**: es (Spanish)
- **自动检测**: auto (仅作为源语言)

### 输出格式选项

- **DOCX**: Microsoft Word文档格式
- **PDF**: 便携式文档格式
- **Both**: 同时生成DOCX和PDF

### 布局模式

- **Side by Side**: 原文和译文并排显示
- **Paragraph by Paragraph**: 原文段落后紧跟译文段落

### 设置分数阈值

```json
"score_threshold_enabled": true,
"score_threshold": 0.7
```

### DeepSeek翻译配置示例

#### DeepSeek Chat 模型（标准翻译）

使用DeepSeek Chat翻译服务的配置文件示例：

```json
{
  "translation_settings": {
    "provider": "deepseek",
    "api_key": "YOUR_DEEPSEEK_API_KEY",
    "model": "deepseek-chat",
    "source_language": "auto",
    "target_language": "zh-CN",
    "temperature": 0.1,
    "batch_size": 10,
    "delay_between_requests": 1.0
  },
  "output_settings": {
    "format": "docx",
    "layout": "side_by_side",
    "replace_original": false
  }
}
```

#### DeepSeek Reasoner 模型（高质量推理翻译）

使用DeepSeek Reasoner翻译服务的配置文件示例：

```json
{
  "translation_settings": {
    "provider": "deepseek-reasoner",
    "api_key": "YOUR_DEEPSEEK_API_KEY",
    "model": "deepseek-reasoner",
    "source_language": "auto",
    "target_language": "zh-CN",
    "temperature": 0.1,
    "batch_size": 5,
    "delay_between_requests": 2.0
  },
  "output_settings": {
    "format": "docx",
    "layout": "side_by_side",
    "replace_original": false
  }
}
```

#### 模型选择建议

**DeepSeek Chat (`deepseek`)**：
- 适用场景：日常文档、商务邮件、技术文档
- 优势：响应速度快、成本较低、适合大批量翻译
- 推荐用于：常规翻译任务

**DeepSeek Reasoner (`deepseek-reasoner`)**：
- 适用场景：学术论文、法律文档、复杂技术文档
- 优势：深度推理能力、更高翻译质量、更好的上下文理解
- 推荐用于：需要高质量翻译的专业文档
- 注意：响应时间较长、成本较高

### 使用方法

1. 获取DeepSeek API密钥：访问 [DeepSeek官网](https://platform.deepseek.com/) 注册并获取API密钥
2. 在Web界面中选择翻译提供商：
   - 选择 "deepseek" 使用标准Chat模型
   - 选择 "deepseek-reasoner" 使用推理模型
3. 输入您的API密钥
4. 选择源语言和目标语言
5. 上传PDF文件开始翻译

### 批量测试大量用例

对于大量测试用例，建议：

1. 增加请求间隔时间避免API限流
2. 分批次执行测试
3. 使用配置文件管理参数

## 🚨 注意事项

1. **API限流**: 请根据您的API配额设置合适的请求间隔
2. **数据安全**: 不要在代码中硬编码API密钥
3. **网络稳定**: 确保网络连接稳定，避免测试中断
4. **结果备份**: 重要的测试结果请及时备份

## 🐛 故障排除

### 常见问题：

1. **API认证失败**
   - 检查API密钥是否正确
   - 确认API密钥有访问指定知识库的权限

2. **网络连接超时**
   - 检查网络连接
   - 增加请求超时时间
   - 减少并发请求数量

3. **CSV文件格式错误**
   - 确保CSV文件编码为UTF-8
   - 检查列名是否正确
   - 确保必需字段不为空

4. **依赖包安装失败**
   - 使用虚拟环境
   - 更新pip版本
   - 检查Python版本兼容性

## 📝 示例工作流程

1. **准备测试数据**
   ```bash
   # 使用提供的示例文件或创建自己的测试用例
   cp test_cases_sample.csv my_test_cases.csv
   ```

2. **配置API参数**
   ```bash
   cp config_template.json my_config.json
   # 编辑my_config.json，填入真实的API信息
   ```

3. **执行测试**
   ```bash
   python enhanced_recall_tester.py \
     --config my_config.json \
     --test-file my_test_cases.csv \
     --output-dir ./my_results \
     --generate-viz
   ```

4. **分析结果**
   - 查看CSV文件了解总体情况
   - 查看JSON文件了解详细信息
   - 查看生成的图表进行可视化分析

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个工具！

## 📄 许可证

MIT License