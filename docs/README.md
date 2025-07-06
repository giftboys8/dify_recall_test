# 项目文档中心

欢迎来到知识库召回测试与翻译平台的文档中心！本目录包含了项目的完整文档，帮助您快速了解和使用本项目。

## 📚 文档导航

### 🚀 快速开始
- [项目目录结构](./project-structure.md) - 了解项目的整体架构
- [安装指南](./installation-guide.md) - 详细的安装步骤和故障排除

### 🔧 开发文档
- [代码质量指南](./development/code-quality-guide.md) - 代码质量改进建议和最佳实践
- [翻译功能开发](./development/translation-development.md) - 翻译功能的技术实现

### 📋 项目报告
- [依赖优化报告](./reports/requirements-optimization.md) - 项目依赖包的优化记录

### 🎯 功能特性

#### 核心功能
- **知识库召回测试** - 批量测试Dify知识库的召回效果
- **文档翻译处理** - 支持PDF、PPT等多种格式的翻译
- **Web界面管理** - 提供友好的Web操作界面
- **数据统一管理** - 统一的数据库管理系统

#### 支持格式
- PDF文档处理和翻译
- PowerPoint演示文稿处理
- CSV测试用例管理
- JSON配置文件管理

## 🛠️ 技术栈

### 后端技术
- **Python 3.8+** - 主要开发语言
- **Flask** - Web框架
- **SQLite** - 数据存储
- **Transformers** - AI模型支持

### 前端技术
- **HTML/CSS/JavaScript** - Web界面
- **Streamlit** - 快速Web应用开发

### AI/ML技术
- **OpenAI API** - GPT模型支持
- **NLLB** - 多语言翻译模型
- **DeepSeek** - 推理和翻译模型

## 📖 使用指南

### 命令行工具
```bash
# 主程序入口
python main.py --help

# 快速启动
python quick_start.py

# Web界面
python web_interface.py
```

### 配置管理
- 主配置文件：`config.json`
- 翻译配置：`config/translation_config.json`
- 示例配置：`examples/translation_config_complete.json`

## 🔍 故障排除

### 常见问题
1. **依赖安装失败** - 参考[安装指南](./installation-guide.md)
2. **翻译功能异常** - 查看[翻译功能开发](./development/translation-development.md)
3. **Web界面无法启动** - 检查Streamlit依赖安装

### 获取帮助
- 查看项目README.md
- 检查相关文档
- 查看代码注释

## 📝 贡献指南

### 开发环境设置
1. 克隆项目仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 运行测试：`pytest`
4. 启动开发服务器

### 代码规范
- 遵循PEP 8代码风格
- 添加适当的注释和文档字符串
- 编写单元测试
- 参考[代码质量指南](./development/code-quality-guide.md)

## 📊 项目状态

- ✅ 核心功能完整
- ✅ 文档体系完善
- ✅ 测试覆盖良好
- 🔄 持续优化中

---

*最后更新：2024年*
*如有问题或建议，欢迎提交Issue或Pull Request*