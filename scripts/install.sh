#!/bin/bash

# Dify知识库召回测试工具 - 安装脚本

echo "🚀 Dify知识库召回测试工具 - 安装脚本"
echo "================================================"

# 检查Python版本
echo "🐍 检查Python版本..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
if [[ -z "$python_version" ]]; then
    echo "❌ 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

echo "✅ Python版本: $python_version"

# 检查pip
echo "📦 检查pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ 未找到pip3，请先安装pip"
    exit 1
fi

echo "✅ pip已安装"

# 创建虚拟环境（可选）
read -p "🔧 是否创建虚拟环境? (推荐) (y/n) [y]: " create_venv
create_venv=${create_venv:-y}

if [[ "$create_venv" == "y" ]]; then
    echo "📁 创建虚拟环境..."
    python3 -m venv venv
    
    echo "🔌 激活虚拟环境..."
    source venv/bin/activate
    
    echo "✅ 虚拟环境已创建并激活"
    echo "💡 下次使用前请运行: source venv/bin/activate"
fi

# 升级pip
echo "⬆️ 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📦 安装Python依赖包..."
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
    echo "✅ 依赖包安装完成"
else
    echo "❌ 未找到requirements.txt文件"
    echo "手动安装依赖包..."
    pip install requests pandas matplotlib seaborn streamlit plotly openpyxl
fi

# 检查安装
echo "🔍 验证安装..."
python3 -c "
import requests, pandas, matplotlib, seaborn, streamlit, plotly
print('✅ 所有依赖包安装成功')
" 2>/dev/null

if [[ $? -eq 0 ]]; then
    echo "🎉 安装完成！"
    echo ""
    echo "📋 下一步:"
    echo "1. 运行快速启动脚本: python3 quick_start.py"
    echo "2. 或启动Web界面: streamlit run web_interface.py"
    echo "3. 或查看README.md了解详细使用方法"
    echo ""
    echo "💡 提示:"
    if [[ "$create_venv" == "y" ]]; then
        echo "- 每次使用前请激活虚拟环境: source venv/bin/activate"
    fi
    echo "- 准备好您的Dify API密钥和知识库ID"
    echo "- 可以使用test_cases_sample.csv作为示例测试用例"
else
    echo "❌ 安装验证失败，请检查错误信息"
    exit 1
fi