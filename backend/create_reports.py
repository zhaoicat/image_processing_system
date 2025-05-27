#!/usr/bin/env python3
"""
为所有已完成的任务创建报告记录
"""

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

import glob
from tasks.models import Task, Report
from django.conf import settings

def create_missing_reports():
    """为所有已完成的任务创建缺失的报告记录"""
    
    # 直接扫描reports目录中的HTML文件
    html_files = glob.glob(os.path.join(settings.REPORTS_DIR, 'task_*/*.html'))
    print(f'找到 {len(html_files)} 个HTML报告文件')

    created_count = 0
    for html_file in html_files:
        # 从文件路径中提取任务ID
        task_id_match = os.path.basename(os.path.dirname(html_file)).replace('task_', '')
        try:
            task_id = int(task_id_match)
            task = Task.objects.get(id=task_id)
            
            # 检查是否已存在报告记录
            if not Report.objects.filter(task=task).exists():
                # 创建报告记录
                report = Report(
                    title=f'{task.name} - 质量检测报告',
                    task=task,
                    file_path=html_file
                )
                report.save()
                created_count += 1
                print(f'为任务 {task.id} ({task.status}) 创建了报告记录: {os.path.basename(html_file)}')
            else:
                existing_report = Report.objects.filter(task=task).first()
                print(f'任务 {task.id} ({task.status}) 已有报告记录: {existing_report.title[:50]}...')
                
        except (ValueError, Task.DoesNotExist) as e:
            print(f'跳过无效的HTML文件: {html_file} - {e}')

    print(f'\n总共创建了 {created_count} 个报告记录')
    print(f'当前报告总数: {Report.objects.count()}')

if __name__ == '__main__':
    create_missing_reports() 