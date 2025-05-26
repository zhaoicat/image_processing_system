from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from typing import List, Any

api_patterns = [
    path('images/', include('images.urls')),
    path('tasks/', include('tasks.urls')),
    path('reports/', include('reports.urls')),
    path('auth/', include('users.urls')),
]

urlpatterns: List[Any] = [
    path('admin/', admin.site.urls),
    path('api/', include(api_patterns)),
]

# 在开发环境中添加媒体文件服务
if settings.DEBUG:
    # 直接添加静态文件URL
    urlpatterns += static(
        settings.MEDIA_URL, 
        document_root=settings.MEDIA_ROOT
    ) 