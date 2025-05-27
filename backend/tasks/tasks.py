"""
图像处理模块 - V2现代化版本

直接调用final2中的V2现代化处理逻辑
"""

import os
import time
import json
import logging
import threading
import glob
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 导入V2现代化处理函数 - 使用简单的导入方式
def get_process_images_function():
    """动态导入process_images函数，避免启动时的导入错误"""
    try:
        from final2.api_integration import process_images
        return process_images
    except ImportError as e:
        logging.warning(f"无法导入process_images函数: {e}")
        # 返回一个模拟函数，避免启动错误
        def mock_process_images(*args, **kwargs):
            return {"status": "error", "message": "process_images函数不可用"}
        return mock_process_images

# 使用Django配置的日志记录器
logger = logging.getLogger(__name__)


def update_task_status_file(report_dir, status, progress=0, message=None):
    """
    更新任务状态文件
    参数:
        report_dir: 报告目录路径
        status: 任务状态，可选值: 'pending', 'processing', 'completed', 'failed'
        progress: 处理进度 (0-100)
        message: 状态信息或错误信息
    """
    # 确保目录存在
    os.makedirs(report_dir, exist_ok=True)

    # 状态文件路径
    status_file = os.path.join(report_dir, "task_status.json")

    # 更新状态数据
    status_data = {
        "status": status,
        "progress": progress,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    if message:
        status_data["message"] = message

    # 写入状态文件
    try:
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        logger.debug(
            "已更新任务状态文件: %s, 状态: %s, 进度: %s%%",
            status_file, status, progress
        )
    except (IOError, OSError, json.JSONDecodeError) as e:
        logger.error("更新任务状态文件失败: %s", str(e))


def _process_task_async(task_data):
    """
    异步处理任务的内部函数
    
    参数:
        task_data: 包含任务信息的字典
    """
    # 获取任务参数
    task_id = task_data.get("task_id")
    algorithm_choice = task_data.get("algorithm_choice", "5")
    report_dir = task_data.get("report_dir")
    image_paths = task_data.get("image_paths", [])

    logger.info("开始异步处理任务: %s", task_id)

    try:
        # 更新状态为处理中
        update_task_status_file(
            report_dir, "processing", 10, 
            "正在使用V2现代化算法处理..."
        )
        
        # 调用V2处理函数 - 使用正确的路径配置
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        process_images = get_process_images_function()
        result = process_images(
            image_paths=image_paths,
            output_dir=report_dir,
            algorithm_choice=algorithm_choice,
            custom_paths={
                'template_image_dir': os.path.join(base_dir, 'final2', 'data', 'template'),
                'comparison_image_dir': os.path.dirname(image_paths[0]) if image_paths else report_dir,
                'report_dir': report_dir
            }
        )
        
        if result["status"] == "success":
            logger.info("任务 %s V2处理成功", task_id)
            update_task_status_file(
                report_dir, "completed", 100, "V2现代化处理完成"
            )
            
            # 自动创建报告记录 - 为每个生成的报告文件创建记录
            try:
                from tasks.models import Report, Task
                
                # 获取任务对象
                task = Task.objects.get(id=task_id)
                
                # 查找生成的HTML报告文件
                html_files = glob.glob(os.path.join(report_dir, "*.html"))
                
                if html_files:
                    # 算法名称映射
                    algorithm_names = {
                        '图像准确度': '图像准确度AI检测（ImageHash算法）',
                        '图像质量': '图像质量AI检测（Opencv算法1）',
                        '图像纹理': '图像纹理质量AI检测（Opencv算法2）',
                        '图像清晰度': '图像清晰度AI检测（Opencv+ScikitImage算法3）',
                        '综合质量AI检测': '综合质量AI检测'
                    }
                    
                    created_reports = []
                    for html_file in html_files:
                        # 从文件名提取报告类型
                        filename = os.path.basename(html_file)
                        report_type = None
                        
                        for key in algorithm_names.keys():
                            if key in filename:
                                report_type = algorithm_names[key]
                                break
                        
                        if not report_type:
                            report_type = "质量检测报告"
                        
                        # 创建报告记录
                        report = Report(
                            title=f"{task.name} - {report_type}",
                            task=task,
                            file_path=html_file
                        )
                        report.save()
                        created_reports.append(report)
                        logger.info("任务 %s 报告记录已创建: %s - %s", task_id, report_type, html_file)
                    
                    logger.info("任务 %s 共创建了 %d 个报告记录", task_id, len(created_reports))
                else:
                    logger.warning("任务 %s 未找到HTML报告文件", task_id)
                    
            except Exception as e:
                logger.error("任务 %s 创建报告记录失败: %s", task_id, str(e))
        else:
            error_msg = result.get("message", "V2处理失败")
            logger.error("任务 %s V2处理失败: %s", task_id, error_msg)
            update_task_status_file(
                report_dir, "failed", 0, f"V2处理失败: {error_msg}"
            )
            
    except Exception as e:
        logger.error("任务 %s V2处理时出错: %s", task_id, str(e))
        update_task_status_file(
            report_dir, "failed", 0, f"V2处理异常: {str(e)}"
        )


def submit_task(task_data):
    """
    提交任务到V2现代化处理（异步）

    参数:
        task_data: 包含任务信息的字典，包括:
            - task_id: 任务ID
            - algorithm_choice: 算法选择
            - report_dir: 报告输出目录
            - image_paths: 图像路径列表

    返回:
        bool: 是否成功提交任务（立即返回，不等待处理完成）
    """
    logger.info("提交任务: %s （使用V2现代化处理，异步模式）", task_data['task_id'])

    # 获取任务参数
    task_id = task_data.get("task_id")
    algorithm_choice = task_data.get("algorithm_choice", "5")
    report_dir = task_data.get("report_dir")
    image_paths = task_data.get("image_paths", [])

    # 打印任务参数用于调试
    logger.info("任务参数:")
    logger.info("task_id: %s", task_id)
    logger.info("algorithm_choice: %s", algorithm_choice)
    logger.info("report_dir: %s", report_dir)
    logger.info("image_paths: %s", image_paths)

    # 初始化任务状态
    update_task_status_file(report_dir, "pending", 0, "任务已提交，等待处理")

    if not image_paths:
        logger.error("任务 %s 没有图片", task_id)
        update_task_status_file(report_dir, "failed", 0, "任务没有图片")
        return False

    try:
        # 创建并启动异步处理线程
        thread = threading.Thread(
            target=_process_task_async,
            args=(task_data,),
            name=f"TaskProcessor-{task_id}",
            daemon=True  # 设置为守护线程，主程序退出时自动结束
        )
        thread.start()
        
        logger.info("任务 %s 已成功提交到异步处理队列", task_id)
        return True
        
    except Exception as e:
        logger.error("提交任务 %s 到异步队列失败: %s", task_id, str(e))
        update_task_status_file(
            report_dir, "failed", 0, f"提交任务失败: {str(e)}"
        )
        
        # 调用V2处理函数 - 使用正确的路径配置
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        process_images = get_process_images_function()
        result = process_images(
            image_paths=image_paths,
            output_dir=report_dir,
            algorithm_choice=algorithm_choice,
            custom_paths={
                'template_image_dir': os.path.join(base_dir, 'final2', 'data', 'template'),
                'comparison_image_dir': os.path.dirname(image_paths[0]) if image_paths else report_dir,
                'report_dir': report_dir
            }
        )
        
        if result["status"] == "success":
            logger.info("任务 %s V2处理成功", task_id)
            update_task_status_file(
                report_dir, "completed", 100, "V2现代化处理完成"
            )
            
            # 自动创建报告记录 - 为每个生成的报告文件创建记录
            try:
                from tasks.models import Report, Task
                
                # 获取任务对象
                task = Task.objects.get(id=task_id)
                
                # 查找生成的HTML报告文件
                html_files = glob.glob(os.path.join(report_dir, "*.html"))
                
                if html_files:
                    # 算法名称映射
                    algorithm_names = {
                        '图像准确度': '图像准确度AI检测（ImageHash算法）',
                        '图像质量': '图像质量AI检测（Opencv算法1）',
                        '图像纹理': '图像纹理质量AI检测（Opencv算法2）',
                        '图像清晰度': '图像清晰度AI检测（Opencv+ScikitImage算法3）',
                        '综合质量AI检测': '综合质量AI检测'
                    }
                    
                    created_reports = []
                    for html_file in html_files:
                        # 从文件名提取报告类型
                        filename = os.path.basename(html_file)
                        report_type = None
                        
                        for key in algorithm_names.keys():
                            if key in filename:
                                report_type = algorithm_names[key]
                                break
                        
                        if not report_type:
                            report_type = "质量检测报告"
                        
                        # 创建报告记录
                        report = Report(
                            title=f"{task.name} - {report_type}",
                            task=task,
                            file_path=html_file
                        )
                        report.save()
                        created_reports.append(report)
                        logger.info("任务 %s 报告记录已创建: %s - %s", task_id, report_type, html_file)
                    
                    logger.info("任务 %s 共创建了 %d 个报告记录", task_id, len(created_reports))
                else:
                    logger.warning("任务 %s 未找到HTML报告文件", task_id)
                    
            except Exception as e:
                logger.error("任务 %s 创建报告记录失败: %s", task_id, str(e))
            return True
        else:
            error_msg = result.get("message", "V2处理失败")
            logger.error("任务 %s V2处理失败: %s", task_id, error_msg)
            update_task_status_file(
                report_dir, "failed", 0, f"V2处理失败: {error_msg}"
            )
            return False
            
    except Exception as e:
        logger.error("任务 %s V2处理时出错: %s", task_id, str(e))
        update_task_status_file(
            report_dir, "failed", 0, f"V2处理异常: {str(e)}"
        )
        return False
