#!/usr/bin/env python3
"""
图像处理API集成模块
提供与Django后端的集成接口
"""

import os
import logging
from typing import List, Dict, Any, Optional
from .config import get_config, get_paths
from .utils import evaluation

logger = logging.getLogger(__name__)


def process_images(
    image_paths: List[str],
    output_dir: str,
    algorithm_choice: str = "12345",
    template_image_path: Optional[str] = None,
    custom_config: Optional[Dict[str, Any]] = None,
    custom_paths: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    处理图像并生成报告
    
    Args:
        image_paths: 要处理的图像路径列表
        output_dir: 输出目录
        algorithm_choice: 算法选择，默认"12345"表示所有算法
        template_image_path: 模板图像路径（可选）
        custom_config: 自定义配置参数（可选）
        custom_paths: 自定义路径配置（可选）
    
    Returns:
        Dict: 处理结果，包含报告路径等信息
    """
    try:
        logger.info(f"开始处理图像，算法选择: {algorithm_choice}")
        logger.info(f"要处理的图像数量: {len(image_paths)}")
        
        # 获取默认配置并应用自定义配置
        config = get_config()
        if custom_config:
            config.update(custom_config)
        
        # 获取默认路径配置并应用自定义配置
        paths = get_paths()
        if custom_paths:
            paths.update(custom_paths)
        
        # 更新路径配置
        paths.update({
            'comparison_image_dir': (os.path.dirname(image_paths[0])
                                     if image_paths else output_dir),
            'report_dir': output_dir
        })
        
        # 如果提供了模板图像路径，使用它
        if template_image_path:
            paths['template_image_dir'] = os.path.dirname(template_image_path)
        
        logger.info(f"配置参数: {config}")
        logger.info(f"路径配置: {paths}")
        
        # 调用评估函数，传递具体的图像路径列表
        result = evaluation(
            paths=paths,
            config=config,
            input_choice=algorithm_choice,
            specific_image_paths=image_paths  # 传递具体的图像路径列表
        )
        
        logger.info("图像处理完成")
        return result
        
    except Exception as e:
        logger.error(f"图像处理失败: {e}")
        raise


if __name__ == "__main__":
    # 测试代码
    test_paths = [
        "data/template/2.jpg",
        "data/comparision/1.jpg"
    ]
    
    result = process_images(
        image_paths=test_paths,
        output_dir="test_output"
    )
    
    print("测试结果:", result) 