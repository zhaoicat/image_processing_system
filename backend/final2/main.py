#!/usr/bin/env python3
"""
图像处理系统主程序
使用统一的配置文件
"""

import sys
import os
import logging
from config import get_config, get_paths

# 添加当前目录到Python路径，支持直接运行
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils import evaluation

# 配置日志
logger = logging.getLogger(__name__)

# 使用统一的配置
paths = get_paths()
config = get_config()

def process_images(task_id, algorithm_choice, output_dir, image_paths):
    """
    处理图像的主函数，集成算法包装器和报告生成
    
    参数:
        task_id: 任务ID
        algorithm_choice: 算法选择 (如 "1", "12", "1234" 等)
        output_dir: 输出目录
        image_paths: 图像路径列表
    
    返回:
        dict: 包含处理结果的字典
    """
    try:
        logger.info(f"开始处理任务 {task_id}，算法选择: {algorithm_choice}")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 如果只有一张图片，使用第一张作为模板和比较图片
        if len(image_paths) == 1:
            template_path = image_paths[0]
            comparison_path = image_paths[0]
        elif len(image_paths) >= 2:
            template_path = image_paths[0]
            comparison_path = image_paths[1]
        else:
            return {
                "status": "error",
                "message": "没有足够的图片进行处理"
            }
        
        # 配置路径
        paths = {
            'template_image_dir': os.path.dirname(template_path),
            'comparison_image_dir': os.path.dirname(comparison_path),
            'report_dir': output_dir
        }
        
        # 使用原有的evaluation函数生成报告
        evaluation(paths, config, algorithm_choice)
        
        return {
            "status": "success",
            "message": f"任务 {task_id} 处理完成",
            "output_dir": output_dir
        }
        
    except Exception as e:
        logger.error(f"处理任务 {task_id} 时出错: {str(e)}")
        return {
            "status": "error",
            "message": f"处理失败: {str(e)}"
        }

if __name__ == '__main__':
    print("功能说明：")
    print("1. 图像准确度AI检测报告（ImageHash算法）")
    print("2. 图像质量AI检测报告（Opencv算法1）")
    print("3. 图像纹理质量AI检测报告（Opencv算法2）")
    print("4. 清晰度AI检测报告（Opencv+ScikitImage算法3）")
    print("5. 整体图像质量AI检测报告（功能1+2+3+4）")
    print("6. generate_prompt")
    print("7. 异常图像数据生成")
    print("0. 退出程序")
    while True:
        input_choice = input("请输入功能选择（例如：'12' 表示功能1和2）：")
        if input_choice == '0':
            print("退出程序")
            break
        evaluation(paths, config, input_choice)