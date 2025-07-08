# Docker 部署指南

本项目提供了完整的 Docker 容器化解决方案，支持开发和生产环境部署。

## 📁 Docker 相关文件

- `Dockerfile` - 主应用容器构建文件
- `docker-compose.yaml` - 生产环境编排配置
- `docker-compose.dev.yaml` - 开发环境覆盖配置
- `.dockerignore` - Docker 构建忽略文件
- `nginx.conf` - Nginx 反向代理配置

## 🚀 快速开始

### 1. 生产环境部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f kb-app
```

### 2. 开发环境部署

```bash
# 使用开发环境配置
docker-compose -f docker-compose.yaml -f docker-compose.dev.yaml up -d

# 启动开发工具（可选）
docker-compose --profile tools up -d
```

## 🌐 服务端口

| 服务 | 端口 | 描述 |
|------|------|------|
| 主应用 | 8080 | Web 服务器主界面 |
| API 服务 | 5000 | Flask API 接口 |
| Streamlit | 8501 | 交互式 Web 界面 |
| Redis | 6379 | 缓存服务 |
| Nginx | 80/443 | 反向代理（生产环境） |
| Redis Commander | 8081 | Redis 管理界面（开发环境） |

## 📂 数据持久化

以下目录会被挂载到宿主机，确保数据持久化：

- `./data` - 数据库文件和处理结果
- `./uploads` - 用户上传的文件
- `./config` - 配置文件
- `./logs` - 应用日志
- `./static` - 静态资源文件
- `./templates` - HTML 模板文件

## 🔧 配置管理

### 环境变量

在 `docker-compose.yaml` 中可以配置以下环境变量：

```yaml
environment:
  - PYTHONUNBUFFERED=1      # Python 输出不缓冲
  - LOG_LEVEL=INFO           # 日志级别
  - PYTHONPATH=/app/src      # Python 路径
  - TOKENIZERS_PARALLELISM=false  # 禁用 tokenizers 并行
```

### 配置文件

将配置文件放在 `./config/` 目录下：

```bash
# 复制示例配置
cp examples/translation_config_complete.json config/translation_config.json

# 编辑主配置
vim config.json
```

## 🛠️ 常用命令

### 服务管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart kb-app

# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f
```

### 容器操作

```bash
# 进入应用容器
docker-compose exec kb-app bash

# 运行命令
docker-compose exec kb-app python main.py --help

# 查看容器资源使用
docker stats
```

### 数据管理

```bash
# 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz data/ uploads/ config/

# 清理数据
docker-compose down -v  # 删除 volumes

# 重建容器
docker-compose up --build -d
```

## 🔍 故障排除

### 1. 容器启动失败

```bash
# 查看详细日志
docker-compose logs kb-app

# 检查容器状态
docker-compose ps

# 重建镜像
docker-compose build --no-cache kb-app
```

### 2. 端口冲突

修改 `docker-compose.yaml` 中的端口映射：

```yaml
ports:
  - "8081:8080"  # 将主机端口改为 8081
```

### 3. 权限问题

```bash
# 修复文件权限
sudo chown -R $USER:$USER data/ uploads/ logs/
chmod -R 755 data/ uploads/ logs/
```

### 4. 内存不足

在 `docker-compose.yaml` 中限制内存使用：

```yaml
services:
  kb-app:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

## 🏭 生产环境部署

### 1. 启用 Nginx 反向代理

```bash
# 启动包含 Nginx 的完整服务
docker-compose --profile production up -d
```

### 2. SSL 证书配置

```bash
# 创建 SSL 目录
mkdir -p ssl/

# 放置证书文件
cp your-cert.pem ssl/cert.pem
cp your-key.pem ssl/key.pem

# 取消注释 nginx.conf 中的 HTTPS 配置
```

### 3. 环境变量配置

创建 `.env` 文件：

```bash
# .env
LOG_LEVEL=WARNING
DEBUG=0
FLASK_ENV=production
```

## 📊 监控和日志

### 健康检查

```bash
# 检查应用健康状态
curl http://localhost:8080/health

# 查看 Docker 健康状态
docker-compose ps
```

### 日志管理

```bash
# 查看最近日志
docker-compose logs --tail=100 kb-app

# 持续监控日志
docker-compose logs -f kb-app

# 导出日志
docker-compose logs kb-app > app.log
```

## 🔄 更新和维护

### 应用更新

```bash
# 拉取最新代码
git pull

# 重建并重启服务
docker-compose up --build -d

# 清理旧镜像
docker image prune -f
```

### 数据库迁移

```bash
# 运行迁移脚本
docker-compose exec kb-app python tools/migrate_to_unified_db.py
```

## 📝 注意事项

1. **首次启动**：确保 `data/`、`uploads/`、`config/` 目录存在
2. **配置文件**：启动前请配置 `config.json` 中的 API 密钥
3. **防火墙**：确保相关端口在防火墙中开放
4. **资源限制**：根据服务器配置调整内存和 CPU 限制
5. **备份策略**：定期备份 `data/` 和 `uploads/` 目录

## 🆘 获取帮助

如果遇到问题，请：

1. 查看应用日志：`docker-compose logs kb-app`
2. 检查容器状态：`docker-compose ps`
3. 查看系统资源：`docker stats`
4. 参考项目文档：`docs/` 目录
5. 提交 Issue 并附上相关日志信息