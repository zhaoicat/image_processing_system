#!/usr/bin/env python

"""
测试脚本：验证任务日志API是否正常工作
使用方法：python test_log_api.py <task_id>
"""

import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_processing_system.settings')
django.setup()

from tasks.models import Task
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_task_log_api(task_id):
    """测试获取任务日志"""
    try:
        # 获取任务
        task = Task.objects.get(id=task_id)
        logger.info(f"找到任务: {task.name} (ID: {task.id})")
        logger.info(f"任务状态: {task.status}")
        logger.info(f"算法: {task.algorithms if task.algorithms else task.algorithm}")
        
        # 检查日志文件路径
        log_file_path = f"/tmp/task_{task_id}.log"
        if os.path.exists(log_file_path):
            logger.info(f"找到日志文件: {log_file_path}")
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    logger.info(f"日志内容长度: {len(content)} 字符")
                    logger.info("日志预览（前200字符）:")
                    print(content[:200])
                else:
                    logger.warning("日志文件为空")
        else:
            logger.warning(f"日志文件不存在: {log_file_path}")
            
        # 检查debug.log中的相关日志
        debug_log_path = os.path.join(os.path.dirname(__file__), 'debug.log')
        if os.path.exists(debug_log_path):
            logger.info(f"检查debug.log文件: {debug_log_path}")
            with open(debug_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                task_related_lines = [line for line in lines if f"task_{task_id}" in line or f"任务ID={task_id}" in line]
                logger.info(f"在debug.log中找到 {len(task_related_lines)} 行相关日志")
                if task_related_lines:
                    logger.info("相关日志示例:")
                    for line in task_related_lines[-3:]:  # 显示最后3行
                        print(line.strip())
        else:
            logger.warning(f"debug.log文件不存在: {debug_log_path}")
            
    except Task.DoesNotExist:
        logger.error(f"任务ID {task_id} 不存在")
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")

def main():
    if len(sys.argv) != 2:
        print("使用方法：python test_log_api.py <task_id>")
        print("示例：python test_log_api.py 172")
        sys.exit(1)
    
    try:
        task_id = int(sys.argv[1])
    except ValueError:
        print("错误：任务ID必须是数字")
        sys.exit(1)
    
    print(f"🔍 开始测试任务 {task_id} 的日志API...")
    test_task_log_api(task_id)
    print("✅ 测试完成")

if __name__ == "__main__":
    main() 