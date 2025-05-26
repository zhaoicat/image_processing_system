#!/bin/bash

# 彩色日志Django服务器启动脚本
# 使用方法: ./start_server_colorlog.sh [端口号]

# 设置默认端口
PORT=${1:-8888}

echo "🚀 启动Django服务器 (彩色日志版)"
echo "📍 端口: $PORT"
echo "🎨 日志级别颜色说明:"
echo "   🔵 DEBUG: 青色"
echo "   🟢 INFO: 绿色" 
echo "   🟡 WARNING: 黄色"
echo "   🔴 ERROR: 红色"
echo "   ⚪ CRITICAL: 红色背景白字"
echo "=" * 50

# 确保我们在正确的目录
cd "$(dirname "$0")"

# 设置Django配置模块
export DJANGO_SETTINGS_MODULE=image_processing.settings

# 启动服务器
echo "🔄 正在启动服务器..."
python manage.py runserver $PORT

echo "👋 服务器已停止" 