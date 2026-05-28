FROM python:3.11-slim

RUN pip install --no-cache-dir uv

WORKDIR /app/backend

# 先复制依赖定义，利用 Docker 缓存层
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --no-dev --no-install-project

# 复制后端代码
COPY backend/ .

# 生成 RSA 密钥对（脚本会自动跳过已存在的密钥）
RUN uv run app/utils/init_keys.py

EXPOSE 9910
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9910", "--workers", "2"]
