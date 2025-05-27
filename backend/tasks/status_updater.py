import os
import json
import logging
from django.conf import settings
from .models import Task
from django.utils import timezone
from django.db import transaction


# 获取日志记录器
logger = logging.getLogger(__name__)


def update_task_status():
    """
    更新所有任务的状态
    该方法会检查各个任务的状态文件，并更新数据库中的任务状态
    建议定期执行此方法（例如通过Celery计划任务或在API请求时调用）
    """
    logger.debug("开始更新任务状态")
    tasks_updated = 0
    
    # 获取处于处理中的任务
    tasks = Task.objects.filter(status__in=['pending', 'processing'])
    for task in tasks:
        try:
            # 检查任务状态文件
            report_dir = os.path.join(settings.REPORTS_DIR, f"task_{task.id}")
            status_file = os.path.join(report_dir, "task_status.json")
            
            if not os.path.exists(status_file):
                logger.debug(f"任务 {task.id} 状态文件不存在")
                continue
                
            # 读取状态文件
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"任务 {task.id} 状态文件JSON格式错误")
                continue
                
            # 提取状态信息
            file_status = status_data.get('status')
            progress = status_data.get('progress', 0)
            
            # 更新任务状态
            with transaction.atomic():
                # 重新查询任务以获取最新状态
                current_task = Task.objects.select_for_update().get(
                    id=task.id
                )
                
                # 仅当状态需要更改时才更新
                status_changed = (
                    (file_status == 'processing' and
                     current_task.status != 'processing') or
                    (file_status == 'completed' and
                     current_task.status != 'completed') or
                    (file_status == 'failed' and
                     current_task.status != 'failed') or
                    abs(current_task.progress - progress) >= 1.0
                )
                
                if status_changed:
                    # 更新状态和进度
                    current_task.status = file_status
                    current_task.progress = progress
                    
                    # 如果任务完成，设置完成时间
                    if (file_status == 'completed' and
                            not current_task.completed_at):
                        current_task.completed_at = timezone.now()
                        logger.info(f"任务 {current_task.id} 已完成")
                    
                    # 如果任务失败，记录失败原因
                    if file_status == 'failed':
                        current_task.failure_reason = status_data.get(
                            'message', '未知错误'
                        )
                    
                    current_task.save()
                    tasks_updated += 1
                    logger.debug(
                        f"任务 {task.id} 状态已更新: {file_status}, "
                        f"进度: {progress}%"
                    )
        
        except Exception as e:
            logger.error(f"更新任务 {task.id} 状态时出错: {e}")
    
    logger.debug(f"任务状态更新完成，已更新 {tasks_updated} 个任务")
    return tasks_updated
