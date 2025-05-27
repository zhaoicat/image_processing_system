"""
图像处理系统后端包

提供图像处理、任务管理和报告生成功能
"""

# 设置final2包的导入路径
import os
import sys

# 获取当前目录和父目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
final2_dir = os.path.join(parent_dir, "final2")
algorithm_dir = os.path.join(final2_dir, "algorithm")

# 将final2目录添加到Python路径
if final2_dir not in sys.path:
    sys.path.insert(0, final2_dir)
    
# 将algorithm目录添加到Python路径
if algorithm_dir not in sys.path:
    sys.path.insert(0, algorithm_dir)

# 直接从final2导出process_images函数
from final2.api_integration import process_images

# 定义导出的符号
__all__ = ['process_images'] 