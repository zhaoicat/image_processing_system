"""
Final2 图像处理算法模块

提供算法包装器、API集成和报告生成功能
"""

# 导出主要的API函数
from .api_integration import process_images
from .algorithm_wrappers import (
    imagehash_algorithm,
    opencv1_algorithm,
    opencv2_algorithm,
    opencv3_algorithm,
    openai_algorithm,
    anomaly_data_algorithm,
    comprehensive_algorithm
)
from .report_generator import generate_html_report, quick_report_generation

__all__ = [
    'process_images',
    'imagehash_algorithm',
    'opencv1_algorithm', 
    'opencv2_algorithm',
    'opencv3_algorithm',
    'openai_algorithm',
    'anomaly_data_algorithm',
    'comprehensive_algorithm',
    'generate_html_report',
    'quick_report_generation'
]

__version__ = '1.0.0' 