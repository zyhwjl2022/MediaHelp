#!/bin/sh
cd /app/backend

# Alembic 数据库迁移
alembic upgrade head

# 初始化脚本
python3 init.py

# 启动后端
nohup uvicorn main:app --host 0.0.0.0 --port 8001 &

# 启动 nginx
nginx -g "daemon off;" 