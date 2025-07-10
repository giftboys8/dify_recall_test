FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    # libreoffice \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip &&  pip install --no-cache-dir -r requirements.txt

# 安装可选的web界面依赖
RUN pip install --no-cache-dir streamlit>=1.25.0 plotly>=5.15.0 matplotlib>=3.5.0 seaborn>=0.11.0

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p data/input data/output data/notes data/annotations \
    && mkdir -p uploads/documents \
    && mkdir -p logs \
    && mkdir -p config

# 设置权限
RUN chmod +x install.sh

# 暴露端口
# 5000: Flask API服务器
# 8080: Web服务器
# 8501: Streamlit界面
EXPOSE 5000 8082 8501

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV LOG_LEVEL=INFO

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 启动命令
CMD ["python", "main.py", "web", "--host", "0.0.0.0", "--port", "8082"]
