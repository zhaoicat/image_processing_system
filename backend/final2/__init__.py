"""
final2 - 图像处理包

提供图像处理算法和报告生成功能
"""

import os
import sys

# 获取当前目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
algorithm_dir = os.path.join(current_dir, "algorithm")

# 添加algorithm目录到Python路径
if algorithm_dir not in sys.path:
    sys.path.insert(0, algorithm_dir)

# 从main模块导出关键函数
from .main import process_images

# 从utils模块导出常用函数
try:
    from .utils import evaluation
except ImportError:
    # utils模块导入失败时提供占位符
    def evaluation(*args, **kwargs):
        """utils.evaluation函数的占位符"""
        raise NotImplementedError("utils.evaluation函数无法导入")

# 包信息
__version__ = "1.0.0"
__author__ = "Image Processing Team"
__all__ = ["process_images", "evaluation"]

# 导出函数说明
"""
process_images - 处理图像的主函数
Args:
    task_id (str): 任务ID，用于标识当前处理任务
    algorithm_choice (list or str): 算法选择列表或字符串
    output_dir (str): 输出目录路径
    image_paths (list): 图片路径列表
    custom_paths (dict, optional): 自定义路径配置，覆盖默认路径
    custom_config (dict, optional): 自定义配置参数，覆盖默认配置
        
Returns:
    dict: 包含处理结果和报告路径的字典
""" 