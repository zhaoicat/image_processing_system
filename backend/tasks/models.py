from django.db import models
from django.contrib.auth.models import User
from images.models import Image

class Task(models.Model):
    """任务模型"""
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    )
    
    ALGORITHM_CHOICES = (
        ('algorithm1', '灰度处理'),
        ('algorithm2', '边缘检测'),
        ('algorithm3', '物体识别'),
        ('algorithm4', '哈希计算'),
    )
    
    name = models.CharField(max_length=255)
    algorithm = models.CharField(max_length=100, choices=ALGORITHM_CHOICES)
    description = models.TextField(blank=True, null=True)  # 添加描述字段，可用于存储算法选择等信息
    algorithms = models.JSONField(blank=True, null=True)  # 添加算法数组字段，可以存储多个选择的算法
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    images = models.ManyToManyField(Image, related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # 添加自动更新的时间字段
    completed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True, null=True)
    progress = models.FloatField(default=0.0)  # 添加进度字段，表示处理进度（0-100）
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Report(models.Model):
    """报告模型"""
    title = models.CharField(max_length=255)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='reports')
    file_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.task.name}"
