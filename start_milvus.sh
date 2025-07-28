#!/bin/bash

# Milvus Docker 启动脚本
# 用于快速启动Milvus单机版服务器

echo "🚀 启动Milvus向量数据库服务器..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 停止并删除已存在的Milvus容器
echo "🧹 清理已存在的Milvus容器..."
docker stop milvus-standalone 2>/dev/null || true
docker rm milvus-standalone 2>/dev/null || true

# 拉取最新的Milvus镜像
echo "📥 拉取Milvus镜像..."
docker pull milvusdb/milvus:latest

# 启动Milvus容器
echo "🏃‍♂️ 启动Milvus容器..."
docker run -d \
    --name milvus-standalone \
    -p 19530:19530 \
    -p 9091:9091 \
    -v $(pwd)/milvus_data:/var/lib/milvus \
    milvusdb/milvus:latest \
    standalone

# 等待服务启动
echo "⏳ 等待Milvus服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查Milvus服务状态..."
if docker ps | grep -q milvus-standalone; then
    echo "✅ Milvus启动成功！"
    echo "📊 服务信息："
    echo "   - 主端口: localhost:19530"
    echo "   - 管理端口: localhost:9091"
    echo "   - 容器名: milvus-standalone"
    echo "   - 数据目录: ./milvus_data"
    echo ""
    echo "🎬 现在可以运行 'python init_milvus_db.py' 初始化数据库"
    echo "🎯 或直接运行 'python main.py' 启动推荐系统"
else
    echo "❌ Milvus启动失败，请检查Docker日志："
    docker logs milvus-standalone
fi
