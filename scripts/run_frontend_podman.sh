#!/bin/bash

echo "🚀 Starting Frontend Development Environment with Podman..."

# 检查是否安装了 podman-compose
if ! command -v podman-compose &> /dev/null; then
    echo "⚠️  podman-compose not found. Trying to use 'podman compose'..."
    if ! podman compose version &> /dev/null; then
        echo "❌ Error: Neither 'podman-compose' nor 'podman compose' found."
        echo "Please install podman-compose or update podman."
        exit 1
    else
        COMPOSE_CMD="podman compose"
    fi
else
    COMPOSE_CMD="podman-compose"
fi

echo "📦 Building and starting container..."
# 使用 -f 指定刚才创建的开发专用 compose 文件
$COMPOSE_CMD -f docker-compose.dev.yml up --build

echo "✅ Container stopped."
