# ── SQLAgent Docker 镜像 ──
# 基于 Python 3.11 slim 镜像
# 构建: docker build -t sqlagent:latest .
# 运行: docker run -p 8000:8000 --env-file .env sqlagent:latest

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（PyMySQL 是纯 Python，无需额外编译依赖）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建非 root 用户（安全最佳实践）
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 启动服务
CMD ["uvicorn", "sqlagent.main:app", "--host", "0.0.0.0", "--port", "8000"]
