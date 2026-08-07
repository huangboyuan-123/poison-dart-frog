#!/bin/bash
echo "🐸 箭毒蛙 Poison Dart Frog 启动中..."

# 1. 检查并启动 Docker 服务
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker 未运行"
    exit 1
fi

# 2. 启动后端容器
docker compose up -d 2>/dev/null
echo "✓ 后端服务已就绪"

# 3. 等待 API 就绪
echo "等待 API 启动..."
while ! curl -s http://localhost:8000/health >/dev/null 2>&1; do
    sleep 2
done
echo "✓ API 已连接"

# 4. 启动桌面端
python src/sqlagent/desktop_app.py
