# ----------- 前端构建阶段 -----------
FROM node:20 AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install

# 再拷贝源码，构建
COPY frontend/apps/web-antd ./
RUN pnpm run build

# ----------- 后端构建阶段 -----------
FROM python:3.11-slim AS backend-build
WORKDIR /app/backend

# 只拷贝依赖声明文件，利用缓存
COPY backend/pyproject.toml ./
RUN pip install uv
RUN uv pip install --system pyproject.toml

# 再拷贝源码
COPY backend /app/backend

# ----------- 生产镜像 -----------
FROM nginx:alpine

# 前端静态文件
COPY --from=frontend-build /frontend/dist /usr/share/nginx/html

# nginx 配置
COPY frontend/apps/web-antd/nginx.conf /etc/nginx/conf.d/default.conf

# 后端代码
COPY --from=backend-build /app/backend /app/backend

# 安装后端运行依赖
RUN apk add --no-cache python3 py3-pip bash && \
    pip install uv && \
    pip install alembic

# 启动脚本
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80

CMD ["/start.sh"]
