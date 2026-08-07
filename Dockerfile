# 箭毒蛙 Poison Dart Frog — 完整镜像 (后端 + 桌面端)
FROM python:3.11-slim

WORKDIR /app

# 系统依赖 (PySide6 GUI 需要)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libegl1 libgl1 libglib2.0-0 libxkbcommon0 libdbus-1-3 \
    libfontconfig1 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 \
    libxcb-shape0 libxcb-xinerama0 libxcb-xkb1 libxcb-render-util0 \
    libxcb-image0 libxcb-randr0 libxcb-sync1 libxcb-util1 \
    curl && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt PySide6

# 复制项目
COPY . .

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# 启动脚本: 先启动后端, 再启动GUI
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
