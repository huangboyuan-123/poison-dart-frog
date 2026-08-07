#!/bin/bash
# 箭毒蛙 Docker 启动入口
# 1) 后台启动 FastAPI
# 2) 前台启动 GUI 桌面端

echo "🐸 箭毒蛙 Poison Dart Frog 启动中..."

# 启动后端 API (后台)
uvicorn sqlagent.main:app --host 0.0.0.0 --port 8000 &

# 等待后端就绪
echo "⏳ 等待 API 就绪..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "✓ API 已启动"
        break
    fi
    sleep 1
done

# 启动桌面端 (前台, 保持容器运行)
echo "🚀 启动桌面端..."
exec python src/sqlagent/desktop_app.py
