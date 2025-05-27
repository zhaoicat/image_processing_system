from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from typing import List, Any
from rest_framework.routers import DefaultRouter
from tasks.views import ReportViewSet

# 创建reports路由
reports_router = DefaultRouter()
reports_router.register(r'', ReportViewSet)

api_patterns = [
    path('images/', include('images.urls')),
    path('tasks/', include('tasks.urls')),
    path('reports/', include(reports_router.urls)),
    path('auth/', include('users.urls')),
]

urlpatterns: List[Any] = [
    path('admin/', admin.site.urls),
    path('api/', include(api_patterns)),
]

# 在开发环境中添加媒体文件服务
if settings.DEBUG:
    # 添加媒体文件URL（包括上传的图片和报告文件）
    urlpatterns += static(
        settings.MEDIA_URL, 
        document_root=settings.MEDIA_ROOT
    ) 