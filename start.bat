@echo off
chcp 65001 >nul
echo 🐸 箭毒蛙 Poison Dart Frog 启动中...

:: 1. 检查并启动 Docker 服务
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)

:: 2. 启动后端容器（如果在跑则跳过）
docker compose up -d 2>nul
echo ✓ 后端服务已就绪

:: 3. 等待 API 就绪
echo 等待 API 启动...
:wait_loop
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 >nul
    goto wait_loop
)
echo ✓ API 已连接

:: 4. 启动桌面端
python src/sqlagent/desktop_app.py
