from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, create_task, check_all_reports

router = DefaultRouter()
router.register(r'', TaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 