from django.db import models
from django.contrib.auth.models import User

# User模型将使用Django内置的User模型
# 此处不需要定义自定义用户模型，我们可以直接使用默认的User模型进行身份验证

class UserProfile(models.Model):
    """用户资料扩展模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}的个人资料"
