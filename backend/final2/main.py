"""
main.py - 图像处理算法入口模块

提供了process_images函数作为主要接口，用于处理图像和生成报告
现在仅使用V2现代化报告生成器
"""

import sys
import logging
import multiprocessing

# 使用Django配置的日志记录器
logger = logging.getLogger(__name__)


def process_images(task_id, algorithm_choice, output_dir, image_paths,
                   custom_paths=None, custom_config=None):
    """
    供外部调用的图像处理函数 - 仅使用V2现代化报告生成器
    
    Args:
        task_id (str): 任务ID，用于标识当前处理任务
        algorithm_choice (list or str): 算法选择列表或字符串
        output_dir (str): 输出目录路径
        image_paths (list): 图片路径列表
        custom_paths (dict, optional): 自定义路径配置（已弃用，保持向后兼容）
        custom_config (dict, optional): 自定义配置参数（已弃用，保持向后兼容）
        
    Returns:
        dict: 包含处理结果和报告路径的字典
        
    Example:
        >>> from main import process_images
        >>> result = process_images('task001', '12', './output', 
        ...                         ['image1.jpg', 'image2.jpg'])
        >>> print(result['report_path'])
    """
    # 导入必要的模块
    import os
    import re
    import shutil
    import django
    
    try:
        # 记录任务ID
        logger.info("开始处理任务 %s (仅使用V2现代化报告)", task_id)
        
        # 简化的多进程检测逻辑 - 只在真正的多进程worker中跳过
        current_process = multiprocessing.current_process()
        
        # 只有在明确的多进程worker环境中才跳过V2生成
        # 对于Django视图或shell调用，都应该正常执行V2处理
        if (hasattr(current_process, '_target') and 
            current_process._target is not None and
            current_process.name.startswith('ForkPoolWorker')):
            
            logger.warning("检测到多进程worker环境，跳过V2报告生成以避免冲突")
            return {
                "status": "success",
                "report_path": f"./reports/task_{task_id}",
                "result": {"message": "在多进程worker环境中跳过V2报告生成"}
            }
        
        # 设置Django环境
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
        try:
            django.setup()
        except RuntimeError:
            # Django已经配置过，忽略错误
            pass
        
        # 导入V2报告生成器
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        from reports.generators import generate_task_report_from_database
        
        # 从task_id中提取纯数字ID
        numeric_task_id = task_id
        if isinstance(task_id, str):
            # 如果task_id包含非数字字符，尝试提取数字
            match = re.search(r'(\d+)', task_id)
            if match:
                numeric_task_id = int(match.group(1))
            else:
                logger.error("无法从task_id '%s' 提取数字ID", task_id)
                return {
                    "status": "error",
                    "message": f"无效的任务ID格式: {task_id}"
                }
        
        # 🚀 直接使用V2现代化报告生成器
        logger.info("正在为任务 %s 生成V2现代化报告...", task_id)
        v2_success = generate_task_report_from_database(
            numeric_task_id, cleanup_old=True)
        
        if not v2_success:
            logger.error("任务 %s 的V2现代化报告生成失败", task_id)
            return {
                "status": "error",
                "message": f"V2报告生成失败: 任务ID {numeric_task_id}"
            }
        
        logger.info("任务 %s 的V2现代化报告生成成功", task_id)
        
        # 同步到media目录供前端访问
        try:
            from django.conf import settings
            
            source_dir = os.path.join(
                settings.REPORTS_DIR, f"task_{numeric_task_id}")
            target_dir = os.path.join(
                settings.MEDIA_ROOT, "reports", f"task_{numeric_task_id}")
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_dir), exist_ok=True)
            
            # 复制报告到media目录
            if os.path.exists(source_dir):
                if os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                shutil.copytree(source_dir, target_dir)
                logger.info("V2报告已同步到media目录: %s", target_dir)
                
                return {
                    "status": "success",
                    "report_path": target_dir,
                    "result": {"message": "V2现代化报告生成成功"}
                }
            else:
                logger.error("V2报告源目录不存在: %s", source_dir)
                return {
                    "status": "error",
                    "message": "V2报告源目录不存在"
                }
            
        except Exception as e:
            logger.error("同步V2报告到media目录失败: %s", str(e))
            return {
                "status": "error",
                "message": f"同步报告失败: {str(e)}"
            }
        
    except Exception as e:
        logger.error("生成V2现代化报告时出错: %s", str(e))
        return {
            "status": "error",
            "message": f"处理失败: {str(e)}"
        }


def main():
    """主函数，处理命令行参数"""
    # 检查是否为命令行调用
    if len(sys.argv) > 1:
        print("使用V2现代化报告生成器...")
        
        # 命令行参数格式: python main.py algorithm_choice output_dir image1 image2 ...
        input_choice = sys.argv[1]
        output_dir = sys.argv[2]
        image_paths = sys.argv[3:]
        
        print(f"算法选择: {input_choice}")
        print(f"输出目录: {output_dir}")
        print(f"图片数量: {len(image_paths)}")
        
        # 调用V2处理函数
        result = process_images(
            task_id="cmd_" + input_choice,
            algorithm_choice=input_choice,
            output_dir=output_dir,
            image_paths=image_paths
        )
        
        if result["status"] == "success":
            print(f"V2报告生成完成: {result['report_path']}")
        else:
            print(f"V2报告生成失败: {result['message']}")
        return
    
    # 交互模式已简化
    print("V2现代化报告生成器")
    print("使用方法: python main.py <algorithm_choice> <output_dir> <image1> [image2] ...")
    print("示例: python main.py 12 ./output image1.jpg image2.jpg")


if __name__ == "__main__":
    main()
