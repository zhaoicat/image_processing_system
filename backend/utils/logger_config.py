"""
日志配置模块
提供统一的日志配置
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# 日志格式：时间戳 日志级别 [包名:行号] 信息
LOG_FORMAT = "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s"
# 日期格式
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志级别
DEFAULT_LOG_LEVEL = logging.INFO


def get_log_dir():
    """获取或创建日志目录"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def setup_logger(name):
    """
    设置并返回日志记录器
    
    参数:
        name: 日志记录器名称，通常为__name__
    
    返回:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(DEFAULT_LOG_LEVEL)
    
    # 如果已经有处理器，不重复添加
    if logger.hasHandlers():
        return logger
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # 文件处理器
    log_dir = get_log_dir()
    log_file = os.path.join(log_dir, "app.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger