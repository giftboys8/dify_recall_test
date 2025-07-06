# 项目目录结构说明

## 根目录文件

### 核心文件
- `main.py` - 主程序入口，统一的命令行工具
- `quick_start.py` - 交互式快速启动脚本
- `web_interface.py` - Streamlit Web界面
- `install.sh` - 项目安装脚本
- `config.json` - 主配置文件

### 项目配置
- `requirements.txt` - Python依赖包列表
- `setup.py` - 项目安装配置
- `pytest.ini` - 测试框架配置
- `Makefile` - 构建和部署脚本
- `.gitignore` - Git忽略文件配置
- `README.md` - 项目说明文档

## 目录结构

### `/src/` - 源代码目录
包含所有核心功能模块的源代码

### `/config/` - 配置文件目录
- `translation_config.json` - 翻译功能配置

### `/docs/` - 文档目录
- `code_quality_recommendations.md` - 代码质量改进建议
- `installation_report.md` - 安装状态报告
- `requirements_optimization_report.md` - 依赖包优化报告
- `翻译.md` - 翻译功能文档
- `directory_structure.md` - 本文档

### `/tools/` - 工具脚本目录
- `download_nllb_model.py` - NLLB模型下载工具
- `migrate_to_unified_db.py` - 数据库迁移脚本

### `/examples/` - 示例文件目录
- `test_cases_sample.csv` - 测试用例示例
- `translation_config_complete.json` - 完整翻译配置模板

### `/tests/` - 测试代码目录
包含单元测试和集成测试代码

### `/data/` - 数据目录
存储数据库文件、上传文件等

### `/uploads/` - 文件上传目录
存储用户上传的文件

### `/static/` - 静态资源目录
存储CSS、JS、图片等静态文件

### `/templates/` - 模板目录
存储HTML模板文件

## 使用建议

1. **开发者**：主要关注 `/src/` 和 `/tests/` 目录
2. **用户**：使用 `main.py` 或 `quick_start.py` 开始
3. **配置**：参考 `/examples/` 中的示例配置
4. **文档**：查看 `/docs/` 目录了解详细信息
5. **工具**：使用 `/tools/` 中的辅助脚本