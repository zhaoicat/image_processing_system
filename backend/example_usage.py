"""
直接导入final2示例

这个示例展示了如何直接从final2导入函数，无需使用任何额外模块
"""

import os
import logging

# 直接导入process_images函数，不再需要导入final2_import
from final2.main import process_images

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """示例函数，展示如何使用process_images函数"""
    
    # 准备参数
    task_id = "example_task_001"
    algorithm_choice = "1234"  # 使用所有算法
    output_dir = "./example_output"
    image_paths = ["./example_images/test1.jpg"]
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 处理图像
    logger.info(f"开始处理任务: {task_id}")
    try:
        result = process_images(
            task_id=task_id,
            algorithm_choice=algorithm_choice,
            output_dir=output_dir,
            image_paths=image_paths
        )
        
        # 检查结果
        if result["status"] == "success":
            logger.info(f"任务处理成功！报告路径: {result['report_path']}")
        else:
            logger.error(f"任务处理失败: {result.get('message', '未知错误')}")
            
    except Exception as e:
        logger.exception(f"处理过程中出错: {str(e)}")


if __name__ == "__main__":
    main() 