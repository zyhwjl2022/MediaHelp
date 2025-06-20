#!/bin/sh
cd /app/backend

# 设置环境变量
export ENV=prod


# 设置目录权限
chmod -R 755 /app/backend
mkdir -p /app/backend/data /app/backend/logs /app/backend/config
chmod -R 777 /app/backend/data /app/backend/logs /app/backend/config

# Alembic 数据库迁移
alembic upgrade head

# 初始化脚本
python3 init.py --env=prod

# 启动后端
nohup python ./start.py --env=prod &

# 启动 nginx
nginx -g "daemon off;" 