from django.db import models
from django.contrib.auth.models import User
import os

class Image(models.Model):
    """图像模型"""
    title = models.CharField(max_length=255)
    file = models.ImageField(upload_to='images/%Y/%m/%d/')
    image_hash = models.CharField(max_length=255, blank=True, null=True)  # 添加图像哈希字段
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='images')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title
    
    def delete(self, *args, **kwargs):
        """重写delete方法，删除文件系统中的图像文件"""
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs) 