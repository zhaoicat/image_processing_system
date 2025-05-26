#!/usr/bin/env python
"""
独立脚本：为指定任务生成报告
使用方法：python generate_task_report.py <task_id>
"""

import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_processing_system.settings')
django.setup()

from reports.generators import generate_task_report_from_database


def main():
    if len(sys.argv) != 2:
        print("使用方法：python generate_task_report.py <task_id>")
        print("示例：python generate_task_report.py 171")
        sys.exit(1)
    
    try:
        task_id = int(sys.argv[1])
    except ValueError:
        print("错误：任务ID必须是数字")
        sys.exit(1)
    
    print(f"🚀 开始为任务 {task_id} 生成报告...")
    
    try:
        success = generate_task_report_from_database(task_id, cleanup_old=False)
        
        if success:
            print(f"✅ 任务 {task_id} 的报告生成成功！")
            print(f"📁 报告位置：reports/task_{task_id}/")
            print(f"📊 主报告：reports/task_{task_id}/reports/summary.html")
            print(f"🔧 算法报告：reports/task_{task_id}/reports/algorithms/")
            print(f"🖼️ 图片报告：reports/task_{task_id}/reports/images/")
        else:
            print(f"❌ 任务 {task_id} 的报告生成失败！")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 生成报告时发生错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 