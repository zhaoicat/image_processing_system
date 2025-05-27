"""
算法包装器模块
提供统一的算法调用接口
"""

import sys
import os

# 添加当前目录到Python路径，支持直接运行
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 简单的绝对导入
from algorithm.ImageHash import is_similar
from algorithm.Opencv1 import calculate_image_quality
from algorithm.Opencv2 import evaluate_fashion_image
from algorithm.Opencv3 import calculate_composite_score
from algorithm.Openai import generate_prompt
from algorithm.AnomalyData import generate_anomaly_images

import logging


def imagehash_algorithm(template_image_path, comparison_image_path, threshold):
    """
    图像哈希算法包装器
    
    Args:
        template_image_path (str): 模板图像路径
        comparison_image_path (str): 比较图像路径
        threshold (int): 相似度阈值
        
    Returns:
        dict: 包含距离和相似性结果的字典
    """
    if not template_image_path or not comparison_image_path:
        raise ValueError("模板图像路径和比较图像路径不能为空")
    if threshold is None:
        raise ValueError("阈值不能为None")
    
    return is_similar(template_image_path, comparison_image_path, threshold)


def opencv1_algorithm(image_path, target_color):
    """
    OpenCV1图像质量算法包装器
    
    Args:
        image_path (str): 图像路径
        target_color (tuple): 目标颜色RGB值
        
    Returns:
        dict: 包含各种质量指标的字典
    """
    if not image_path:
        raise ValueError("图像路径不能为空")
    if target_color is None:
        raise ValueError("目标颜色不能为None")
    
    return calculate_image_quality(image_path, target_color)


def opencv2_algorithm(template_image_path, comparison_image_path):
    """
    OpenCV2纹理质量算法包装器
    
    Args:
        template_image_path (str): 模板图像路径
        comparison_image_path (str): 比较图像路径
        
    Returns:
        dict: 包含纹理、完整性、质量等评估结果的字典
    """
    if not template_image_path or not comparison_image_path:
        raise ValueError("模板图像路径和比较图像路径不能为空")
    
    return evaluate_fashion_image(template_image_path, comparison_image_path)


def opencv3_algorithm(image_path):
    """
    OpenCV3清晰度算法包装器
    
    Args:
        image_path (str): 图像路径
        
    Returns:
        dict: 包含清晰度评估结果的字典
    """
    if not image_path:
        raise ValueError("图像路径不能为空")
    
    return calculate_composite_score(image_path)


def openai_algorithm(input_image_uid, x_token):
    """
    OpenAI提示生成算法包装器
    
    Args:
        input_image_uid (str): 输入图像UID
        x_token (str): 认证令牌
        
    Returns:
        None: 该函数直接打印结果
    """
    if not input_image_uid or not x_token:
        raise ValueError("图像UID和认证令牌不能为空")
    
    return generate_prompt(input_image_uid, x_token)


def anomaly_data_algorithm(output_dir):
    """
    异常数据生成算法包装器
    
    Args:
        output_dir (str): 输出目录路径
        
    Returns:
        None: 该函数生成异常图像文件
    """
    if not output_dir:
        raise ValueError("输出目录路径不能为空")
    
    return generate_anomaly_images(output_dir)


def comprehensive_algorithm(template_image_path, comparison_image_path, config):
    """
    综合算法包装器 - 运行所有图像分析算法
    
    Args:
        template_image_path (str): 模板图像路径
        comparison_image_path (str): 比较图像路径
        config (dict): 配置参数字典
        
    Returns:
        dict: 包含所有算法结果的字典
    """
    if not template_image_path or not comparison_image_path:
        raise ValueError("模板图像路径和比较图像路径不能为空")
    if not config:
        raise ValueError("配置参数不能为空")
    
    results = {}
    
    # 运行ImageHash算法
    results['imagehash'] = imagehash_algorithm(
        template_image_path, 
        comparison_image_path, 
        config['distance_threshold']
    )
    
    # 运行OpenCV1算法
    results['opencv1'] = opencv1_algorithm(
        comparison_image_path, 
        (255, 255, 255)  # 默认白色目标
    )
    
    # 运行OpenCV2算法
    results['opencv2'] = opencv2_algorithm(
        template_image_path, 
        comparison_image_path
    )
    
    # 运行OpenCV3算法
    results['opencv3'] = opencv3_algorithm(comparison_image_path)
    
    return results 