from rest_framework import serializers
from .models import Task, Report
from images.models import Image
from images.serializers import ImageSerializer

class TaskSerializer(serializers.ModelSerializer):
    images = serializers.PrimaryKeyRelatedField(many=True, queryset=Image.objects.all())
    created_by_username = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    algorithm_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = ('id', 'name', 'algorithm', 'algorithm_display', 'algorithms', 'status', 'status_display', 
                  'images', 'created_by', 'created_by_username', 'created_at', 
                  'completed_at', 'failure_reason', 'progress', 'description')
        read_only_fields = ('id', 'created_by', 'created_at', 'completed_at', 'status', 'failure_reason', 'progress')
    
    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else None
    
    def get_status_display(self, obj):
        return dict(Task.STATUS_CHOICES).get(obj.status)
    
    def get_algorithm_display(self, obj):
        return dict(Task.ALGORITHM_CHOICES).get(obj.algorithm)

class TaskDetailSerializer(TaskSerializer):
    images = ImageSerializer(many=True, read_only=True)

class ReportSerializer(serializers.ModelSerializer):
    """报告序列化器"""
    task_name = serializers.CharField(source='task.name', read_only=True)
    task_id = serializers.IntegerField(source='task.id', read_only=True)
    
    class Meta:
        model = Report
        fields = ['id', 'title', 'task_id', 'task_name', 'file_path', 'created_at']
        read_only_fields = ['id', 'created_at'] 