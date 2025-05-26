"""
图像处理模块 - V2现代化版本

直接调用final2中的V2现代化处理逻辑
"""

import os
import time
import json
import logging

# 导入V2现代化处理函数
from final2.main import process_images

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


def submit_task(task_data):
    """
    提交任务到V2现代化处理

    参数:
        task_data: 包含任务信息的字典，包括:
            - task_id: 任务ID
            - algorithm_choice: 算法选择
            - report_dir: 报告输出目录
            - image_paths: 图像路径列表

    返回:
        bool: 是否成功提交任务
    """
    logger.info("提交任务: %s （使用V2现代化处理）", task_data['task_id'])

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
        # 更新状态为处理中
        update_task_status_file(
            report_dir, "processing", 10, 
            "正在使用V2现代化算法处理..."
        )
        
        # 调用V2处理函数
        result = process_images(
            task_id=str(task_id),
            algorithm_choice=algorithm_choice,
            output_dir=report_dir,
            image_paths=image_paths
        )
        
        if result["status"] == "success":
            logger.info("任务 %s V2处理成功", task_id)
            update_task_status_file(
                report_dir, "completed", 100, "V2现代化处理完成"
            )
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
