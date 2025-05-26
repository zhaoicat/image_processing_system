"""
图像处理后端任务模块 - V2现代化版本

提供V2现代化图像处理和任务管理功能
"""

# 确保正确设置Python路径
import os
import sys

# 获取父目录路径(backend)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_dir = os.path.dirname(backend_dir)
final2_dir = os.path.join(parent_dir, "final2")
algorithm_dir = os.path.join(final2_dir, "algorithm")

# 添加路径
if final2_dir not in sys.path:
    sys.path.insert(0, final2_dir)
if algorithm_dir not in sys.path:
    sys.path.insert(0, algorithm_dir)

# 导出V2现代化API
from .tasks import (
    submit_task,
    update_task_status_file,
)

__all__ = [
    "submit_task",
    "update_task_status_file",
]
