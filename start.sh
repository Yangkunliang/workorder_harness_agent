#!/bin/bash
# 启动服务脚本

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行，请先启动 Docker Desktop"
    exit 1
fi

# 启动 MySQL 容器
echo "启动 MySQL 容器..."
docker start workorder-mysql

# 等待 MySQL 就绪
echo "等待 MySQL 就绪..."
sleep 10

# 验证 MySQL 连接
if ! docker exec workorder-mysql mysql -uroot -proot123 -e "SELECT 1;" > /dev/null 2>&1; then
    echo "错误: MySQL 连接失败"
    exit 1
fi

echo "MySQL 已就绪"

# 停止占用端口 8000 的进程
lsof -ti:8000 | xargs kill -9 2>/dev/null

# 启动服务
echo "启动服务..."
cd "$(dirname "$0")"
source venv/bin/activate
python3 main.py
