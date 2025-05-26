from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        """应用准备完成"""
        # V2现代化处理不需要工作进程，直接处理
        pass
