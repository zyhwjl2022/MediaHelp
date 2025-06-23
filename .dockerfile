# ----------- 前端构建阶段 -----------
FROM node:20 AS frontend-build
WORKDIR /frontend
COPY /frontend ./
RUN npm install -g pnpm@10.11.1 && pnpm install

# 构建前端
RUN pnpm run build

# ----------- 生产镜像 -----------
FROM nginx:alpine

# 前端静态文件
COPY --from=frontend-build /frontend/apps/web-antd/dist /usr/share/nginx/html

# nginx 配置
COPY frontend/apps/web-antd/nginx.conf /etc/nginx/conf.d/default.conf

# 后端代码（排除.venv目录）
COPY backend /app/backend

# 进入后端目录
WORKDIR /app/backend

# 以 root 用户运行
USER root
# 安装后端运行依赖
RUN apk update && apk add --no-cache python3 py3-pip

# 创建Python符号链接确保可执行文件可用
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.4.15 /uv /bin/uv 

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/backend/.venv/bin:$PATH"

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# 设置授权码环境变量，默认为空
ENV AUTH_CODE=""

# Install dependencies
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# 启动脚本
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80
ENV TZ=Asia/Shanghai

CMD ["/start.sh"]
