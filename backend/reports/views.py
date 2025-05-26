from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Report
from .serializers import ReportSerializer, ReportDetailSerializer
from django.http import FileResponse
import os
import mimetypes
import re
from tasks.models import Task
import logging
from django.conf import settings

# 获取日志记录器
logger = logging.getLogger(__name__)

class ReportViewSet(viewsets.ModelViewSet):
    """报告视图集"""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        """只返回当前用户的任务的报告，支持按任务ID过滤"""
        queryset = Report.objects.filter(task__created_by=self.request.user)
        
        # 支持通过任务ID过滤
        task_id = self.request.query_params.get('task', None)
        if task_id is not None:
            queryset = queryset.filter(task_id=task_id)
        
        return queryset
    
    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'retrieve':
            return ReportDetailSerializer
        return ReportSerializer
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载报告文件"""
        report = self.get_object()
        file_path = report.file_path
        
        if not os.path.exists(file_path):
            return Response({'error': '文件不存在'}, status=404)
            
        # 确定文件类型
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'  # 默认二进制流
        
        # 返回文件
        return FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            as_attachment=True,
            filename=os.path.basename(file_path)
        )
        
    @action(detail=True, methods=['get'])
    def output_log(self, request, pk=None):
        """获取任务的实际输出日志"""
        report = self.get_object()
        task_id = report.task.id
        
        logger.info(f"获取任务 {task_id} 的输出日志")
        
        # 获取任务信息和算法
        task_info = self._get_task_info(task_id)
        log_content = task_info
        logs_found = False
        
        # 收集所有日志
        log_sections = [
            self._get_output_logs(report.file_path),
            self._get_app_logs(task_id),
            self._get_report_results(report.file_path)
        ]
        
        # 将所有非空日志添加到内容中
        for section in log_sections:
            if section[0]:  # 如果找到了日志
                log_content += section[1]
                logs_found = True
        
        # 如果没有找到任何日志
        if not logs_found:
            log_content += "未找到与此任务相关的日志信息。\n"
            
        return Response(log_content, content_type='text/plain')
    
    def _get_task_info(self, task_id):
        """获取任务信息，包括算法列表"""
        try:
            task = Task.objects.get(id=task_id)
            
            # 获取算法信息，优先使用algorithms数组
            if task.algorithms and len(task.algorithms) > 0:
                # 算法名称映射
                algorithm_names = {
                    '1': '图像准确度',
                    '2': '图像质量',
                    '3': '图像纹理',
                    '4': '清晰度'
                }
                alg_display = []
                for alg in task.algorithms:
                    if alg in algorithm_names:
                        alg_display.append(f"{alg}:{algorithm_names[alg]}")
                    else:
                        alg_display.append(alg)
                algorithms_info = ", ".join(alg_display)
            else:
                # 兼容旧数据，使用algorithm字段
                algorithms_info = task.algorithm
                
            return (f"# 任务ID: {task.id}\n"
                    f"# 任务名称: {task.name}\n"
                    f"# 算法: {algorithms_info}\n"
                    f"# 状态: {task.status}\n\n")
        except Exception as e:
            logger.error(f"获取任务信息出错: {str(e)}")
            return f"# 任务ID: {task_id}\n# 获取任务详情失败: {str(e)}\n\n"
    

    
    def _get_output_logs(self, file_path):
        """获取任务输出日志"""
        try:
            report_dir = os.path.dirname(file_path)
            output_file = os.path.join(report_dir, 'output.log')
            
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            return True, "## 任务输出日志\n\n" + content + "\n\n"
                except Exception as e:
                    logger.error(f"读取输出日志文件错误: {str(e)}")
                    return True, f"## 读取输出日志文件错误\n{str(e)}\n\n"
        except Exception as e:
            logger.error(f"查找报告目录日志错误: {str(e)}")
            return True, f"## 查找报告目录日志错误\n{str(e)}\n\n"
            
        return False, ""
    
    def _get_app_logs(self, task_id):
        """获取应用日志"""
        debug_log_path = os.path.join(settings.BASE_DIR, 'debug.log')
        if not os.path.exists(debug_log_path):
            return False, ""
            
        try:
            task_id_patterns = [f"task_{task_id}", f"任务ID={task_id}", f"ID={task_id}"]
            logs = self._extract_logs_by_patterns(debug_log_path, task_id_patterns)
            
            if logs:
                return True, "## 应用日志\n\n" + "".join(logs)
        except Exception as e:
            logger.error(f"读取debug.log文件错误: {str(e)}")
            return True, f"## 读取debug.log文件错误\n{str(e)}\n\n"
            
        return False, ""
    
    def _get_report_results(self, file_path):
        """从报告中提取结果"""
        if not os.path.exists(file_path):
            return False, ""
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                pattern = r'<div class="result">(.*?)</div>'
                results = re.findall(pattern, html_content)
                
                if results:
                    result_text = "## 处理结果\n\n"
                    for result in results:
                        result_text += f"{result.strip()}\n"
                    return True, result_text
        except Exception as e:
            logger.error(f"读取HTML报告文件错误: {str(e)}")
            return True, f"## 读取HTML报告文件错误\n{str(e)}\n\n"
            
        return False, ""
    
    def _extract_logs_by_patterns(self, log_file, patterns):
        """根据模式提取日志行"""
        matched_logs = []
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if any(pattern in line for pattern in patterns):
                    matched_logs.append(line)
                    
        return matched_logs
