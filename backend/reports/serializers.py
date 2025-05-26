from rest_framework import serializers
from .models import Report
from tasks.serializers import TaskSerializer

class ReportSerializer(serializers.ModelSerializer):
    task_name = serializers.SerializerMethodField()
    coverage_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = ('id', 'title', 'task', 'task_name', 'file_path', 'generated_at', 'coverage_data')
        read_only_fields = ('id', 'generated_at')
    
    def get_task_name(self, obj):
        return obj.task.name if obj.task else None
        
    def get_coverage_data(self, obj):
        """获取报告的覆盖率数据"""
        return obj.get_coverage_data()
        
class ReportDetailSerializer(ReportSerializer):
    task = TaskSerializer(read_only=True) 