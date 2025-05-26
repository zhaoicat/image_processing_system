import os
import json
import time
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
    reports_generated = 0
    
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
                        
                        # 任务完成，尝试生成V2报告
                        try:
                            success, message = create_report_for_task(
                                current_task.id
                            )
                            if success:
                                logger.info(
                                    f"为完成的任务 {current_task.id} "
                                    f"成功生成V2报告"
                                )
                                reports_generated += 1
                            else:
                                logger.warning(
                                    f"为完成的任务 {current_task.id} "
                                    f"生成V2报告失败: {message}"
                                )
                        except Exception as e:
                            logger.error(
                                f"为任务 {current_task.id} 生成V2报告时出错: {e}"
                            )
                    
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
    
    logger.debug(
        f"任务状态更新完成，已更新 {tasks_updated} 个任务，"
        f"创建 {reports_generated} 个报告"
    )
    return tasks_updated, reports_generated

def create_report_for_task(task_id):
    """
    为指定任务创建报告记录（仅使用V2现代化逻辑）
    
    参数:
        task_id: 任务ID
        
    返回:
        (success, message) 元组，success是布尔值表示是否成功，
        message是描述信息
    """
    try:
        # 获取任务，增加重试机制处理状态同步延迟
        task = Task.objects.get(id=task_id)
        
        # 检查是否已存在报告记录（优先检查，避免重复生成）
        from reports.models import Report
        if Report.objects.filter(task=task).exists():
            return False, "报告记录已存在"
        
        # 更灵活的状态检查：允许从文件状态推断任务完成
        report_dir = os.path.join(settings.REPORTS_DIR, f"task_{task_id}")
        status_file = os.path.join(report_dir, "task_status.json")
        
        task_completed = task.status == 'completed'
        
        # 如果数据库状态不是completed，检查文件状态
        if not task_completed and os.path.exists(status_file):
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
                file_status = status_data.get('status')
                if file_status == 'completed':
                    # 文件状态是completed，同步更新数据库
                    task.status = 'completed'
                    task.progress = status_data.get('progress', 100)
                    if not task.completed_at:
                        task.completed_at = timezone.now()
                    task.save()
                    task_completed = True
                    logger.info(f"任务 {task_id} 状态已从文件同步到数据库")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"读取任务 {task_id} 状态文件失败: {e}")
        
        # 检查任务是否已完成
        if not task_completed:
            return False, "任务尚未完成，无法创建报告"
        
        # 使用V2逻辑生成现代化报告
        try:
            from reports.generators import generate_task_report_from_database
            logger.info(f"正在为任务 {task_id} 使用V2逻辑生成现代化报告...")
            
            success = generate_task_report_from_database(
                task_id, cleanup_old=True
            )
            
            if success:
                # V2报告生成成功，创建报告记录
                v2_report_dir = os.path.join(
                    settings.REPORTS_DIR, f"task_{task_id}"
                )
                v2_summary_file = os.path.join(
                    v2_report_dir, "reports", "summary.html"
                )
                
                if os.path.exists(v2_summary_file):
                    # 创建报告记录，指向新的V2报告
                    report = Report(
                        title=f"{task.name} - V2现代化报告",
                        task=task,
                        file_path=v2_summary_file
                    )
                    report.save()
                    
                    # 同步到media目录供前端访问
                    try:
                        import shutil
                        media_target_dir = os.path.join(
                            settings.MEDIA_ROOT, "reports", f"task_{task_id}"
                        )
                        
                        # 确保media目录存在
                        os.makedirs(
                            os.path.dirname(media_target_dir), exist_ok=True
                        )
                        
                        # 复制到media目录
                        if os.path.exists(media_target_dir):
                            shutil.rmtree(media_target_dir)
                        shutil.copytree(v2_report_dir, media_target_dir)
                        
                        logger.info(f"任务 {task_id} 的V2报告已同步到media目录")
                        
                    except Exception as e:
                        logger.warning(f"同步报告到media目录失败: {e}")
                        # 不影响主流程，继续执行
                    
                    logger.info(
                        f"为任务 {task_id} 成功创建了V2现代化报告记录"
                    )
                    return True, "V2现代化报告创建成功"
                else:
                    logger.error(
                        f"V2报告生成成功但找不到summary.html文件: "
                        f"{v2_summary_file}"
                    )
                    return False, "V2报告文件不存在"
            else:
                logger.error(f"任务 {task_id} 的V2报告生成失败")
                return False, "V2报告生成失败"
                
        except Exception as e:
            logger.error(f"生成V2报告时出错: {e}")
            return False, f"V2报告生成失败: {str(e)}"
    
    except Task.DoesNotExist:
        return False, "任务不存在"
    except Exception as e:
        logger.error(f"为任务 {task_id} 创建报告记录失败: {e}")
        return False, f"创建报告失败: {str(e)}"

def task_report_mapping_check():
    """
    检查所有任务和报告的对应关系，确保每个已完成的任务都有对应的报告
    
    返回:
        (fixed_count, error_count) 元组，表示修复的数量和错误数量
    """
    fixed_count = 0
    error_count = 0
    
    logger.info("开始检查任务和报告的对应关系")
    
    # 获取所有已完成的任务
    completed_tasks = Task.objects.filter(status='completed')
    
    for task in completed_tasks:
        try:
            # 检查报告文件是否存在
            report_dir = os.path.join(settings.REPORTS_DIR, f"task_{task.id}")
            report_file = os.path.join(report_dir, "report.html")
            
            # 从报告模型获取系统
            from reports.models import Report
            
            # 检查是否已存在报告记录
            if (not Report.objects.filter(task=task).exists() and
                    os.path.exists(report_file)):
                # 创建报告记录
                report = Report(
                    title=f"任务 {task.name} 的报告",
                    task=task,
                    file_path=report_file
                )
                report.save()
                fixed_count += 1
                logger.info(f"为任务 {task.id} 创建了缺失的报告记录")
        
        except Exception as e:
            logger.error(f"检查任务 {task.id} 报告时出错: {e}")
            error_count += 1
    
    logger.info(
        f"任务和报告对应关系检查完成，修复了 {fixed_count} 个报告，"
        f"发生 {error_count} 个错误"
    )
    return fixed_count, error_count
