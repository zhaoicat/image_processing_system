#!/bin/bash
# 启动脚本，确保正确配置Django的设置模块

# 确保运行在正确的目录
cd "$(dirname "$0")"

# 显式设置Django设置模块
export DJANGO_SETTINGS_MODULE=image_processing.settings

# 启动服务器
python manage.py runserver 8888 