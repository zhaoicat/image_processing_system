from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Task
from .serializers import TaskSerializer, TaskDetailSerializer
from .tasks import submit_task
from .status_updater import update_task_status, create_report_for_task
import logging
import os
import threading
import time
import re
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

# 获取日志记录器
logger = logging.getLogger(__name__)

# 创建一个线程锁用于状态更新
status_update_lock = threading.Lock()
last_update_time = 0
UPDATE_INTERVAL = 1.0  # 状态更新间隔秒数


def check_and_update_status():
    """检查并更新任务状态，带有时间间隔控制"""
    global last_update_time
    
    current_time = time.time()
    with status_update_lock:
        if current_time - last_update_time >= UPDATE_INTERVAL:
            try:
                update_task_status()
                last_update_time = current_time
                logger.debug("任务状态已更新")
                return True
            except Exception as e:
                logger.error(f"【错误】更新任务状态失败: {str(e)}")
                return False
    return False



class TaskViewSet(viewsets.ModelViewSet):
    """任务视图集"""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        """只返回当前用户的任务"""
        # 在返回任务列表前更新任务状态
        check_and_update_status()
        return Task.objects.filter(created_by=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """获取单个任务详情前更新任务状态"""
        check_and_update_status()
        return super().retrieve(request, *args, **kwargs)
    
    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'retrieve':
            return TaskDetailSerializer
        return TaskSerializer
    
    def perform_create(self, serializer):
        """创建任务时设置创建者为当前用户并启动任务处理"""
        task_name = serializer.validated_data.get('name')
        logger.info(f"【调试】创建任务: {task_name}")
        
        # 创建任务
        task = serializer.save(created_by=self.request.user, status='pending')
        
        # 创建报告目录
        report_dir = os.path.join(settings.REPORTS_DIR, f"task_{task.id}")
        os.makedirs(report_dir, exist_ok=True)
        
        # 直接使用用户提供的算法数组
        task.algorithms = serializer.validated_data.get('algorithms')
        algorithm_choice = ''.join(sorted(task.algorithms))
     
        
        # 保存算法信息
        task.save()
            
        logger.info(f"【调试】选择的算法: {algorithm_choice}")
        
        # 处理多个图片
        image_paths = []
        for image in task.images.all():
            # 获取图像路径
            image_path = image.file.path
            # 检查路径是否存在
            if os.path.exists(image_path):
                image_paths.append(image_path)
                logger.info(f"【调试】有效图像路径: {image_path}")
            else:
                logger.warning(f"【警告】图像路径不存在: {image_path}")
        
        if image_paths:
            # 提交任务到处理队列 - 传递所有图片路径
            task_data = {
                'task_id': task.id,
                'algorithm_choice': algorithm_choice,
                'report_dir': report_dir,
                'image_paths': image_paths  # 传递所有图片路径
            }
            
            # 记录任务数据
            logger.info(f"【调试】提交任务数据: task_id={task.id}, 算法={algorithm_choice}, 图片数量={len(image_paths)}")
            
            submit_task(task_data)
            logger.info(f"【调试】任务已成功加入处理队列")
        else:
            logger.error(f"【错误】任务没有图片: {task.id}")
            task.status = 'failed'
            task.failure_reason = "没有有效的图片"
            task.save()
    
    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        """重新启动任务，允许重启失败、待处理或处理中的任务"""
        logger.info(f"【调试】尝试重启任务: ID={pk}")
        
        # 使用分布式锁防止并发重启同一个任务
        lock_key = f"task_restart_lock_{pk}"
        # 尝试获取锁，设置锁的过期时间为60秒
        acquired = cache.add(lock_key, "1", timeout=60)
        
        if not acquired:
            logger.warning(f"【调试】任务正在处理中，无法重复提交: ID={pk}")
            return Response(
                {'error': '任务正在处理中，请勿重复提交'}, 
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        try:
            with transaction.atomic():
                # 获取任务对象并锁定行
                task = Task.objects.select_for_update().get(pk=pk)
                
                # 验证任务所有者
                if task.created_by != request.user:
                    logger.warning(f"【调试】权限验证失败: 任务所有者不匹配")
                    return Response(
                        {'error': '没有权限操作此任务'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                logger.info(f"【调试】当前任务状态: {task.status}, 算法: {task.algorithm}, 名称: {task.name}")
                
                # 允许重启处理中的任务
                if task.status not in ['failed', 'pending', 'processing']:
                    logger.warning(f"【调试】任务状态不允许重启: {task.status}")
                    return Response(
                        {'error': '只能重启失败、待处理或处理中的任务'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 简化算法处理逻辑
                
                # 1. 优先使用请求中的算法数组
                task.algorithms = request.data.get('algorithms')
                algorithm_choice = ''.join(sorted(task.algorithms))
                logger.info(f"【调试】使用请求中的算法数组: {task.algorithms}")
                
                
                # 保存原始状态
                original_status = task.status
                logger.info(f"【调试】原始任务状态: {original_status}")
                
                # 重置进度和状态
                task.progress = 0.0
                if original_status == 'failed':
                    task.failure_reason = None
                
                task.status = 'pending'
                task.save()
                logger.info(f"【调试】重置任务状态完成，新状态: {task.status}")
            
            # 短暂延迟，确保数据库事务已提交
            time.sleep(0.1)
            
            # 创建报告目录
            report_dir = os.path.join(settings.REPORTS_DIR, f"task_{task.id}")
            os.makedirs(report_dir, exist_ok=True)
            
            # 处理多个图片
            image_paths = []
            for image in task.images.all():
                # 获取图像路径
                image_path = image.file.path
                # 检查路径是否存在
                if os.path.exists(image_path):
                    image_paths.append(image_path)
                    logger.info(f"【调试】有效图像路径: {image_path}")
                else:
                    logger.warning(f"【警告】图像路径不存在: {image_path}")
            
            if image_paths:
                # 重新提交任务到处理队列
                task_data = {
                    'task_id': task.id,
                    'algorithm_choice': algorithm_choice,
                    'report_dir': report_dir,
                    'image_paths': image_paths  # 传递所有图片路径
                }
                
                # 记录任务数据
                logger.info(f"【调试】重新提交任务数据: task_id={task.id}, 算法={algorithm_choice}, 图片数量={len(image_paths)}")
                
                submit_task(task_data)
                logger.info(f"【调试】任务已重新提交到处理队列")
                
                return Response(
                    {'status': '任务已启动'}, 
                    status=status.HTTP_200_OK
                )
            else:
                logger.error(f"【错误】任务没有图片: {task.id}")
                task.status = 'failed'
                task.failure_reason = "没有有效的图片"
                task.save()
                return Response(
                    {'error': '任务没有有效的图片'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Task.DoesNotExist:
            logger.error(f"【调试】任务不存在: ID={pk}")
            return Response(
                {'error': '任务不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"【调试】重启任务时发生错误: {str(e)}")
            return Response(
                {'error': f'重启任务失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # 释放锁
            cache.delete(lock_key)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取任务的日志内容"""
        task = self.get_object()
        
        # 尝试查找和读取任务的日志文件
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        task_log_file = os.path.join(log_dir, f'task_{task.id}.log')
        logger.info(f"尝试获取任务日志: {task_log_file}")
        
        if os.path.exists(task_log_file):
            try:
                with open(task_log_file, 'r', encoding='utf-8') as log_file:
                    log_content = log_file.read()
                    return Response(log_content, content_type='text/plain')
            except Exception as e:
                logger.error(f"读取任务日志失败: {e}")
                return Response(
                    f"读取任务日志失败: {str(e)}", 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    content_type='text/plain'
                )
        else:
            # 如果找不到专门的日志文件，尝试从系统日志中提取该任务的日志条目
            try:
                system_log_file = os.path.join(log_dir, 'debug.log')
                if os.path.exists(system_log_file):
                    with open(system_log_file, 'r', encoding='utf-8') as log_file:
                        # 查找包含任务ID的日志行
                        log_lines = []
                        for line in log_file:
                            if f"任务 {task.id}" in line or f"ID={task.id}" in line or f"task_{task.id}" in line:
                                log_lines.append(line)
                        
                        if log_lines:
                            return Response(
                                "### 系统日志摘录 ###\n\n" + ''.join(log_lines), 
                                content_type='text/plain'
                            )
                        else:
                            return Response(
                                f"未找到与任务 {task.id} 相关的日志", 
                                content_type='text/plain'
                            )
                else:
                    return Response(
                        "找不到系统日志文件", 
                        status=status.HTTP_404_NOT_FOUND, 
                        content_type='text/plain'
                    )
            except Exception as e:
                logger.error(f"读取系统日志失败: {e}")
                return Response(
                    f"读取系统日志失败: {str(e)}", 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    content_type='text/plain'
                )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """获取任务状态，会主动更新任务状态"""
        # 强制更新任务状态
        check_and_update_status()
        
        try:
            task = self.get_object()
            
            # 如果任务已完成但没有报告记录，尝试创建
            if task.status == 'completed':
                from reports.models import Report
                
                # 检查是否已存在报告记录
                if not Report.objects.filter(task=task).exists():
                    # 尝试创建报告记录
                    success, message = create_report_for_task(task.id)
                    if success:
                        logger.info(f"自动为任务 {task.id} 创建了报告记录")
            
            # 返回任务状态
            data = {
                'id': task.id,
                'status': task.status,
                'progress': task.progress,
                'message': task.failure_reason if task.status == 'failed' else None
            }
            
            return Response(data)
        
        except Exception as e:
            logger.error(f"获取任务状态时出错: {str(e)}")
            return Response(
                {'error': '获取任务状态失败'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @action(detail=True, methods=['post'])
    def generate_report(self, request, pk=None):
        """手动触发报告生成"""
        try:
            task = self.get_object()
            
            if task.status != 'completed':
                return Response(
                    {'error': '只能为已完成的任务生成报告'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 强制生成报告
            success, message = create_report_for_task(task.id)
            
            if success:
                return Response({'message': '报告生成成功'})
            else:
                return Response(
                    {'error': message}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            logger.error(f"手动生成报告时出错: {str(e)}")
            return Response(
                {'error': f'生成报告失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@csrf_exempt
@require_http_methods(["POST"])
def create_task(request):
    """
    接收外部系统的任务创建请求
    """
    if request.content_type != 'application/json':
        return JsonResponse({'error': '只接受JSON格式的请求'}, status=400)
    
    try:
        data = json.loads(request.body)
        logger.info(f"接收到外部任务创建请求: {data}")
        
        # 实现外部任务创建逻辑
        # ...
        
        return JsonResponse({'message': '任务创建成功'})
    except Exception as e:
        logger.error(f"处理外部任务创建请求时出错: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def check_all_reports(request):
    """
    检查所有已完成任务的报告记录，自动创建缺失的报告
    """
    try:
        from .status_updater import task_report_mapping_check
        fixed_count, error_count = task_report_mapping_check()
            
        return JsonResponse({
            'message': f'报告检查完成，修复了 {fixed_count} 个报告，发生 {error_count} 个错误',
            'fixed_count': fixed_count,
            'error_count': error_count
        })
    except Exception as e:
        logger.error(f"检查所有报告时出错: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
